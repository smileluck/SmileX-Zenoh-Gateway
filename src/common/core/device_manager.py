"""
设备管理与组网模块
负责设备的发现、心跳管理和设备列表维护
"""

import time
import threading
import uuid
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..config.settings import settings
from ..utils.logger import logger
from .zenoh_session import ZenohSession, Message, MessageType


class DeviceStatus(Enum):
    """
    设备状态枚举
    """
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """
    设备信息数据类
    """
    device_id: str
    device_name: str
    device_type: str
    status: DeviceStatus = DeviceStatus.UNKNOWN
    last_heartbeat: float = 0.0
    ip_address: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)


class DeviceManager:
    """
    设备管理器类
    负责设备发现、心跳管理和设备列表维护
    """

    # Zenoh 键表达式常量
    KEY_HEARTBEAT = "smilex/device/+/heartbeat"
    KEY_DISCOVERY = "smilex/device/discovery"
    KEY_REGISTER = "smilex/device/register"
    KEY_UNREGISTER = "smilex/device/unregister"

    def __init__(self, zenoh_session: ZenohSession):
        """
        初始化设备管理器
        
        Args:
            zenoh_session: Zenoh 会话实例
        """
        self._zenoh = zenoh_session
        self._devices: Dict[str, DeviceInfo] = {}
        self._lock = threading.Lock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._check_thread: Optional[threading.Thread] = None
        self._running = False
        self._device_callbacks: List[Callable[[DeviceInfo, str], None]] = []
        
        logger.info("初始化设备管理器")

    def start(self):
        """
        启动设备管理器
        """
        if self._running:
            logger.warning("设备管理器已在运行")
            return
        
        self._running = True
        
        logger.info("启动设备管理器...")
        
        self._subscribe_to_heartbeat()
        self._subscribe_to_discovery()
        self._declare_register_service()
        self._declare_unregister_service()
        
        self._heartbeat_thread = threading.Thread(
            target=self._send_heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()
        
        self._check_thread = threading.Thread(
            target=self._check_device_status_loop,
            daemon=True
        )
        self._check_thread.start()
        
        self._send_discovery_broadcast()
        
        logger.info("设备管理器已启动")

    def stop(self):
        """
        停止设备管理器
        """
        if not self._running:
            return
        
        logger.info("停止设备管理器...")
        
        self._running = False
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        
        if self._check_thread:
            self._check_thread.join(timeout=2.0)
        
        self._unsubscribe_all()
        
        logger.info("设备管理器已停止")

    def register_device_callback(self, callback: Callable[[DeviceInfo, str], None]):
        """
        注册设备状态变更回调
        
        Args:
            callback: 回调函数，参数为 (设备信息, 变更类型: 'added'|'removed'|'status_changed')
        """
        self._device_callbacks.append(callback)

    def _notify_device_callbacks(self, device: DeviceInfo, change_type: str):
        """
        通知设备状态变更回调
        
        Args:
            device: 设备信息
            change_type: 变更类型
        """
        for callback in self._device_callbacks:
            try:
                callback(device, change_type)
            except Exception as e:
                logger.error(f"设备回调执行失败: {e}", exc_info=True)

    def _subscribe_to_heartbeat(self):
        """订阅心跳消息"""
        
        def heartbeat_callback(msg: Message):
            self._handle_heartbeat(msg)
        
        self._zenoh.subscribe(self.KEY_HEARTBEAT, heartbeat_callback)
        logger.info("已订阅心跳消息")

    def _subscribe_to_discovery(self):
        """订阅发现消息"""
        
        def discovery_callback(msg: Message):
            self._handle_discovery(msg)
        
        self._zenoh.subscribe(self.KEY_DISCOVERY, discovery_callback)
        logger.info("已订阅发现消息")

    def _declare_register_service(self):
        """声明设备注册服务"""
        
        def register_handler(msg: Message) -> Optional[Message]:
            return self._handle_register(msg)
        
        self._zenoh.declare_queryable(self.KEY_REGISTER, register_handler)
        logger.info("已声明设备注册服务")

    def _declare_unregister_service(self):
        """声明设备注销服务"""
        
        def unregister_handler(msg: Message) -> Optional[Message]:
            return self._handle_unregister(msg)
        
        self._zenoh.declare_queryable(self.KEY_UNREGISTER, unregister_handler)
        logger.info("已声明设备注销服务")

    def _unsubscribe_all(self):
        """取消所有订阅和查询服务"""
        self._zenoh.unsubscribe(self.KEY_HEARTBEAT)
        self._zenoh.unsubscribe(self.KEY_DISCOVERY)
        self._zenoh.undeclare_queryable(self.KEY_REGISTER)
        self._zenoh.undeclare_queryable(self.KEY_UNREGISTER)

    def _send_heartbeat_loop(self):
        """发送心跳循环"""
        while self._running:
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"发送心跳失败: {e}", exc_info=True)
            
            time.sleep(settings.heartbeat_interval)

    def _check_device_status_loop(self):
        """检查设备状态循环"""
        while self._running:
            try:
                self._check_device_status()
            except Exception as e:
                logger.error(f"检查设备状态失败: {e}", exc_info=True)
            
            time.sleep(1.0)

    def _send_heartbeat(self):
        """发送心跳消息"""
        device_id = self._zenoh.node_id
        key_expr = f"smilex/device/{device_id}/heartbeat"
        
        msg = Message(
            msg_type=MessageType.HEARTBEAT,
            source_id=device_id,
            payload={
                "timestamp": time.time()
            },
            timestamp=time.time()
        )
        
        self._zenoh.publish(key_expr, msg)
        logger.debug(f"已发送心跳: {device_id}")

    def _send_discovery_broadcast(self):
        """发送发现广播"""
        msg = Message(
            msg_type=MessageType.DISCOVERY,
            source_id=self._zenoh.node_id,
            payload={
                "action": "search",
                "timestamp": time.time()
            },
            timestamp=time.time()
        )
        
        self._zenoh.publish(self.KEY_DISCOVERY, msg)
        logger.info("已发送发现广播")

    def _handle_heartbeat(self, msg: Message):
        """
        处理心跳消息
        
        Args:
            msg: 心跳消息
        """
        device_id = msg.source_id
        
        with self._lock:
            if device_id not in self._devices:
                logger.warning(f"收到未知设备的心跳: {device_id}")
                return
            
            device = self._devices[device_id]
            old_status = device.status
            device.last_heartbeat = time.time()
            device.status = DeviceStatus.ONLINE
            
            if old_status != DeviceStatus.ONLINE:
                logger.info(f"设备 {device_id} 状态变更: {old_status} -> ONLINE")
                self._notify_device_callbacks(device, "status_changed")

    def _handle_discovery(self, msg: Message):
        """
        处理发现消息
        
        Args:
            msg: 发现消息
        """
        source_id = msg.source_id
        action = msg.payload.get("action")
        
        if action == "search" and source_id != self._zenoh.node_id:
            logger.info(f"收到设备搜索请求: {source_id}")
            self._respond_to_discovery(source_id)
        elif action == "announce":
            self._handle_device_announce(msg)

    def _respond_to_discovery(self, target_id: str):
        """
        响应发现请求
        
        Args:
            target_id: 目标设备ID
        """
        with self._lock:
            if self._zenoh.node_id not in self._devices:
                return
            
            device = self._devices[self._zenoh.node_id]
        
        msg = Message(
            msg_type=MessageType.DISCOVERY,
            source_id=self._zenoh.node_id,
            payload={
                "action": "announce",
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "ip_address": device.ip_address,
                "metadata": device.metadata,
                "timestamp": time.time()
            },
            timestamp=time.time()
        )
        
        self._zenoh.publish(self.KEY_DISCOVERY, msg)
        logger.debug(f"已响应发现请求: {target_id}")

    def _handle_device_announce(self, msg: Message):
        """
        处理设备公告
        
        Args:
            msg: 公告消息
        """
        payload = msg.payload
        device_id = payload.get("device_id")
        
        if not device_id or device_id == self._zenoh.node_id:
            return
        
        with self._lock:
            if device_id not in self._devices:
                device = DeviceInfo(
                    device_id=device_id,
                    device_name=payload.get("device_name", device_id),
                    device_type=payload.get("device_type", "unknown"),
                    status=DeviceStatus.ONLINE,
                    last_heartbeat=time.time(),
                    ip_address=payload.get("ip_address"),
                    metadata=payload.get("metadata", {})
                )
                self._devices[device_id] = device
                logger.info(f"发现新设备: {device_id}")
                self._notify_device_callbacks(device, "added")
            else:
                device = self._devices[device_id]
                device.last_heartbeat = time.time()
                device.status = DeviceStatus.ONLINE

    def _handle_register(self, msg: Message) -> Optional[Message]:
        """
        处理设备注册
        
        Args:
            msg: 注册消息
        
        Returns:
            回复消息
        """
        payload = msg.payload
        device_id = payload.get("device_id")
        
        if not device_id:
            return Message(
                msg_type=MessageType.DATA,
                source_id=self._zenoh.node_id,
                payload={"success": False, "error": "Missing device_id"},
                timestamp=time.time()
            )
        
        with self._lock:
            if len(self._devices) >= settings.max_devices:
                return Message(
                    msg_type=MessageType.DATA,
                    source_id=self._zenoh.node_id,
                    payload={"success": False, "error": "Device limit reached"},
                    timestamp=time.time()
                )
            
            device = DeviceInfo(
                device_id=device_id,
                device_name=payload.get("device_name", device_id),
                device_type=payload.get("device_type", "unknown"),
                status=DeviceStatus.ONLINE,
                last_heartbeat=time.time(),
                ip_address=payload.get("ip_address"),
                metadata=payload.get("metadata", {})
            )
            
            is_new = device_id not in self._devices
            self._devices[device_id] = device
            
            if is_new:
                logger.info(f"设备已注册: {device_id}")
                self._notify_device_callbacks(device, "added")
        
        return Message(
            msg_type=MessageType.DATA,
            source_id=self._zenoh.node_id,
            payload={"success": True},
            timestamp=time.time()
        )

    def _handle_unregister(self, msg: Message) -> Optional[Message]:
        """
        处理设备注销
        
        Args:
            msg: 注销消息
        
        Returns:
            回复消息
        """
        payload = msg.payload
        device_id = payload.get("device_id")
        
        if not device_id:
            return Message(
                msg_type=MessageType.DATA,
                source_id=self._zenoh.node_id,
                payload={"success": False, "error": "Missing device_id"},
                timestamp=time.time()
            )
        
        with self._lock:
            if device_id in self._devices:
                device = self._devices.pop(device_id)
                logger.info(f"设备已注销: {device_id}")
                self._notify_device_callbacks(device, "removed")
        
        return Message(
            msg_type=MessageType.DATA,
            source_id=self._zenoh.node_id,
            payload={"success": True},
            timestamp=time.time()
        )

    def _check_device_status(self):
        """检查设备状态，标记超时设备为离线"""
        current_time = time.time()
        timeout = settings.heartbeat_timeout
        
        with self._lock:
            for device_id, device in list(self._devices.items()):
                if device_id == self._zenoh.node_id:
                    continue
                
                if (current_time - device.last_heartbeat) > timeout:
                    old_status = device.status
                    device.status = DeviceStatus.OFFLINE
                    
                    if old_status != DeviceStatus.OFFLINE:
                        logger.warning(f"设备 {device_id} 超时，标记为离线")
                        self._notify_device_callbacks(device, "status_changed")

    def register_self(self, device_name: str, device_type: str, metadata: Optional[Dict[str, str]] = None):
        """
        注册自身设备
        
        Args:
            device_name: 设备名称
            device_type: 设备类型
            metadata: 设备元数据
        """
        with self._lock:
            device = DeviceInfo(
                device_id=self._zenoh.node_id,
                device_name=device_name,
                device_type=device_type,
                status=DeviceStatus.ONLINE,
                last_heartbeat=time.time(),
                metadata=metadata or {}
            )
            self._devices[self._zenoh.node_id] = device
        
        logger.info(f"自身设备已注册: {self._zenoh.node_id}")

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """
        获取设备信息
        
        Args:
            device_id: 设备ID
        
        Returns:
            设备信息，不存在返回 None
        """
        with self._lock:
            return self._devices.get(device_id)

    def get_all_devices(self) -> List[DeviceInfo]:
        """
        获取所有设备信息
        
        Returns:
            设备信息列表
        """
        with self._lock:
            return list(self._devices.values())

    def get_online_devices(self) -> List[DeviceInfo]:
        """
        获取所有在线设备
        
        Returns:
            在线设备列表
        """
        with self._lock:
            return [d for d in self._devices.values() if d.status == DeviceStatus.ONLINE]
