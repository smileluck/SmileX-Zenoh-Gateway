"""
测试设备管理模块
"""

import time
import threading

from smilex_zenoh_gateway.core import (
    ZenohSession,
    Message,
    MessageType,
    DeviceManager,
    DeviceInfo,
    DeviceStatus
)
from logging import getLogger

logger = getLogger(__name__)


def test_device_manager():
    """测试设备管理器基本功能"""
    logger.info("=" * 50)
    logger.info("测试设备管理器")
    
    session1 = ZenohSession(node_id="device-001")
    session2 = ZenohSession(node_id="device-002")
    
    device_added = threading.Event()
    device_status_changed = threading.Event()
    added_device = None
    
    def device_callback(device: DeviceInfo, change_type: str):
        nonlocal added_device
        logger.info(f"设备回调: {change_type} - {device.device_id}")
        if change_type == "added":
            added_device = device
            device_added.set()
        elif change_type == "status_changed":
            device_status_changed.set()
    
    try:
        session1.connect()
        session2.connect()
        
        mgr1 = DeviceManager(session1)
        mgr2 = DeviceManager(session2)
        
        mgr1.register_device_callback(device_callback)
        mgr2.register_device_callback(device_callback)
        
        mgr1.register_self("云端控制平台", "cloud", {"location": "server"})
        mgr2.register_self("测试机器人1", "robot", {"model": "test-001"})
        
        mgr1.start()
        mgr2.start()
        
        logger.info("等待设备发现...")
        time.sleep(3)
        
        devices1 = mgr1.get_all_devices()
        logger.info(f"管理器1 设备数: {len(devices1)}")
        for d in devices1:
            logger.info(f"  - {d.device_id} ({d.status.value})")
        
        devices2 = mgr2.get_all_devices()
        logger.info(f"管理器2 设备数: {len(devices2)}")
        
        assert len(devices1) >= 1, "管理器1应该至少有1台设备"
        assert len(devices2) >= 1, "管理器2应该至少有1台设备"
        
        logger.info("✓ 设备管理器基本测试通过")
        
    finally:
        mgr1.stop()
        mgr2.stop()
        session1.disconnect()
        session2.disconnect()


def main():
    """运行所有测试"""
    logger.info("开始设备管理器测试")
    try:
        test_device_manager()
        logger.info("\n所有测试通过！✓")
    except Exception as e:
        logger.error(f"\n测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
