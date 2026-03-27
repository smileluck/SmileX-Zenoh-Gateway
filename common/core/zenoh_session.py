"""
Zenoh Session 管理模块
负责 Zenoh 会话的创建、管理和基本通信功能
"""

import json
import threading
import time
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
from queue import Queue

import zenoh

from ..config.settings import settings
from ..config.zenoh_config import get_zenoh_config_manager
from logging import getLogger

logger = getLogger(__name__)


class MessageType(Enum):
    """
    消息类型枚举
    """
    DATA = "data"
    COMMAND = "command"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"


@dataclass
class Message:
    """
    消息数据类
    """
    msg_type: MessageType
    source_id: str
    payload: Dict[str, Any]
    timestamp: float
    msg_id: Optional[str] = None


class ZenohSession:
    """
    Zenoh 会话管理类
    """

    def __init__(self, node_id: str, node_type: str):
        """
        初始化 Zenoh 会话管理器
        
        Args:
            node_id: 节点唯一标识符
            node_type: 节点类型，可选值: "api", "cloud", "robot"
        """
        self.node_id = node_id
        self.node_type = node_type.lower()
        self._session: Optional[zenoh.Session] = None
        self._subscribers: Dict[str, zenoh.Subscriber] = {}
        self._queryables: Dict[str, zenoh.Queryable] = {}
        self._publishers: Dict[str, zenoh.Publisher] = {}
        self._is_running = False
        self._lock = threading.Lock()
        self._message_queues: Dict[str, Queue] = {}
        
        self._config_manager = get_zenoh_config_manager(self.node_type)
        
        logger.info(f"初始化 Zenoh 会话管理器，节点ID: {node_id}，节点类型: {self.node_type}")

    def connect(self) -> bool:
        """
        连接到 Zenoh 网络
        
        Returns:
            是否连接成功
        """
        with self._lock:
            if self._session is not None:
                logger.warning("Zenoh 会话已存在")
                return True
            
            try:
                logger.info("正在连接到 Zenoh 网络...")
                
                zenoh_config_dict = self._config_manager.get_zenoh_config()
                
                config = self._dict_to_zenoh_config(zenoh_config_dict)
                
                self._session = zenoh.open(config)
                self._is_running = True
                
                logger.info("Zenoh 会话连接成功")
                return True
                
            except Exception as e:
                logger.error(f"Zenoh 会话连接失败: {e}", exc_info=True)
                self._session = None
                return False

    def _dict_to_zenoh_config(self, config_dict: Dict[str, Any]) -> zenoh.Config:
        """
        将字典转换为 zenoh.Config 对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            zenoh.Config 对象
        """
        config = zenoh.Config()
        
        try:
            if "mode" in config_dict:
                config.insert_json5("mode", json.dumps(config_dict["mode"]))

            if "listen" in config_dict and "endpoints" in config_dict["listen"]:
                endpoints = config_dict["listen"]["endpoints"]
                if endpoints:
                    config.insert_json5("listen/endpoints", json.dumps(endpoints))

            if "connect" in config_dict and "endpoints" in config_dict["connect"]:
                endpoints = config_dict["connect"]["endpoints"]
                if endpoints:
                    config.insert_json5("connect/endpoints", json.dumps(endpoints))
            
            if "scouting" in config_dict:
                for scout_key, scout_val in config_dict["scouting"].items():
                    config.insert_json5(f"scouting/{scout_key}", json.dumps(scout_val))
            
            if "transport" in config_dict:
                for transport_key, transport_val in config_dict["transport"].items():
                    config.insert_json5(f"transport/{transport_key}", json.dumps(transport_val))
            
            if "timestamping" in config_dict:
                config.insert_json5("timestamping", json.dumps(config_dict["timestamping"]))
            
        except Exception as e:
            logger.warning(f"配置转换过程中部分配置可能未生效: {e}")
        
        return config

    def disconnect(self):
        """
        断开 Zenoh 连接
        """
        with self._lock:
            if self._session is None:
                return
            
            try:
                logger.info("正在断开 Zenoh 连接...")
                
                for sub in self._subscribers.values():
                    sub.undeclare()
                self._subscribers.clear()
                
                for q in self._queryables.values():
                    q.undeclare()
                self._queryables.clear()
                
                for pub in self._publishers.values():
                    pub.undeclare()
                self._publishers.clear()
                
                self._session.close()
                self._session = None
                self._is_running = False
                
                logger.info("Zenoh 连接已断开")
                
            except Exception as e:
                logger.error(f"断开 Zenoh 连接时出错: {e}", exc_info=True)

    def publish(
        self,
        key_expr: str,
        message: Message,
        encoding: Optional[zenoh.Encoding] = None
    ) -> bool:
        """
        发布消息
        
        Args:
            key_expr: Zenoh 键表达式
            message: 要发布的消息
            encoding: 消息编码
        
        Returns:
            是否发布成功
        """
        if self._session is None:
            logger.error("Zenoh 会话未连接")
            return False
        
        try:
            msg_dict = {
                "msg_type": message.msg_type.value,
                "source_id": message.source_id,
                "payload": message.payload,
                "timestamp": message.timestamp,
                "msg_id": message.msg_id
            }
            
            payload = json.dumps(msg_dict).encode("utf-8")
            
            if encoding is None:
                encoding = zenoh.Encoding.APPLICATION_JSON
            
            if key_expr not in self._publishers:
                ke = self._session.declare_keyexpr(key_expr)
                publisher = self._session.declare_publisher(ke)
                self._publishers[key_expr] = publisher
            
            self._publishers[key_expr].put(payload, encoding=encoding)
            
            logger.debug(f"消息已发布到 {key_expr}")
            return True
            
        except Exception as e:
            logger.error(f"发布消息失败: {e}", exc_info=True)
            return False

    def subscribe(
        self,
        key_expr: str,
        callback: Callable[[Message], Any],
    ) -> bool:
        """
        订阅消息
        
        Args:
            key_expr: Zenoh 键表达式
            callback: 消息回调函数
        
        Returns:
            是否订阅成功
        """
        if self._session is None:
            logger.error("Zenoh 会话未连接")
            return False
        
        if key_expr in self._subscribers:
            logger.warning(f"已存在该键表达式的订阅: {key_expr}")
            return True
        
        try:
            def zenoh_callback(sample):
                try:
                    payload = bytes(sample.payload).decode("utf-8")
                    msg_dict = json.loads(payload)
                    
                    message = Message(
                        msg_type=MessageType(msg_dict["msg_type"]),
                        source_id=msg_dict["source_id"],
                        payload=msg_dict["payload"],
                        timestamp=msg_dict["timestamp"],
                        msg_id=msg_dict.get("msg_id")
                    )
                    
                    callback(message)
                    
                except Exception as e:
                    logger.error(f"处理订阅消息失败: {e}", exc_info=True)
            
            ke = self._session.declare_keyexpr(key_expr)
            subscriber = self._session.declare_subscriber(ke, zenoh_callback)
            
            self._subscribers[key_expr] = subscriber
            logger.info(f"成功订阅: {key_expr}")
            return True
            
        except Exception as e:
            logger.error(f"订阅失败: {e}", exc_info=True)
            return False

    def unsubscribe(self, key_expr: str):
        """
        取消订阅
        
        Args:
            key_expr: Zenoh 键表达式
        """
        if key_expr in self._subscribers:
            try:
                self._subscribers[key_expr].undeclare()
                del self._subscribers[key_expr]
                logger.info(f"已取消订阅: {key_expr}")
            except Exception as e:
                logger.error(f"取消订阅失败: {e}", exc_info=True)

    def query(
        self,
        key_expr: str,
        message: Message,
        timeout: float = 5.0
    ) -> Optional[Message]:
        """
        发送查询并等待回复
        
        Args:
            key_expr: Zenoh 键表达式
            message: 查询消息
            timeout: 超时时间（秒）
        
        Returns:
            回复消息，超时返回 None
        """
        if self._session is None:
            logger.error("Zenoh 会话未连接")
            return None
        
        try:
            msg_dict = {
                "msg_type": message.msg_type.value,
                "source_id": message.source_id,
                "payload": message.payload,
                "timestamp": message.timestamp,
                "msg_id": message.msg_id
            }
            
            payload = json.dumps(msg_dict).encode("utf-8")
            
            ke = self._session.declare_keyexpr(key_expr)
            replies = self._session.get(
                ke,
                payload=payload,
                encoding=zenoh.Encoding.APPLICATION_JSON,
                timeout=timeout
            )
            
            for reply in replies:
                if reply.ok:
                    try:
                        reply_payload = bytes(reply.ok.payload).decode("utf-8")
                        reply_dict = json.loads(reply_payload)
                        
                        return Message(
                            msg_type=MessageType(reply_dict["msg_type"]),
                            source_id=reply_dict["source_id"],
                            payload=reply_dict["payload"],
                            timestamp=reply_dict["timestamp"],
                            msg_id=reply_dict.get("msg_id")
                        )
                    except Exception as e:
                        logger.error(f"解析查询回复失败: {e}", exc_info=True)
            
            logger.warning(f"查询未收到回复: {key_expr}")
            return None
            
        except Exception as e:
            logger.error(f"查询失败: {e}", exc_info=True)
            return None

    def declare_queryable(
        self,
        key_expr: str,
        callback: Callable[[Message], Optional[Message]]
    ) -> bool:
        """
        声明查询服务
        
        Args:
            key_expr: Zenoh 键表达式
            callback: 查询处理回调函数，返回回复消息
        
        Returns:
            是否声明成功
        """
        if self._session is None:
            logger.error("Zenoh 会话未连接")
            return False
        
        if key_expr in self._queryables:
            logger.warning(f"已存在该键表达式的查询服务: {key_expr}")
            return True
        
        try:
            def zenoh_query_callback(query):
                try:
                    payload = bytes(query.payload).decode("utf-8")
                    msg_dict = json.loads(payload)
                    
                    message = Message(
                        msg_type=MessageType(msg_dict["msg_type"]),
                        source_id=msg_dict["source_id"],
                        payload=msg_dict["payload"],
                        timestamp=msg_dict["timestamp"],
                        msg_id=msg_dict.get("msg_id")
                    )
                    
                    reply_msg = callback(message)
                    
                    if reply_msg:
                        reply_dict = {
                            "msg_type": reply_msg.msg_type.value,
                            "source_id": reply_msg.source_id,
                            "payload": reply_msg.payload,
                            "timestamp": reply_msg.timestamp,
                            "msg_id": reply_msg.msg_id
                        }
                        reply_payload = json.dumps(reply_dict).encode("utf-8")
                        query.reply(
                            query.key_expr,
                            reply_payload,
                            encoding=zenoh.Encoding.APPLICATION_JSON
                        )
                    
                except Exception as e:
                    logger.error(f"处理查询失败: {e}", exc_info=True)
            
            ke = self._session.declare_keyexpr(key_expr)
            queryable = self._session.declare_queryable(ke, zenoh_query_callback)
            
            self._queryables[key_expr] = queryable
            logger.info(f"成功声明查询服务: {key_expr}")
            return True
            
        except Exception as e:
            logger.error(f"声明查询服务失败: {e}", exc_info=True)
            return False

    def undeclare_queryable(self, key_expr: str):
        """
        取消声明查询服务
        
        Args:
            key_expr: Zenoh 键表达式
        """
        if key_expr in self._queryables:
            try:
                self._queryables[key_expr].undeclare()
                del self._queryables[key_expr]
                logger.info(f"已取消查询服务: {key_expr}")
            except Exception as e:
                logger.error(f"取消查询服务失败: {e}", exc_info=True)

    @property
    def is_connected(self) -> bool:
        """
        是否已连接
        
        Returns:
            连接状态
        """
        return self._session is not None and self._is_running
