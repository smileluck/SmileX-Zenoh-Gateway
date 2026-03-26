"""
机器人端主模块
"""

import sys
import time
import uuid

from common.config.settings import settings
from logging import getLogger

logger = getLogger(__name__)
from common.core import ZenohSession, DeviceManager, Message, MessageType


def main():
    """
    主函数
    """
    logger.info(f"启动 SmileX Zenoh Gateway - 机器人端 v{settings.app_version}")

    try:
        logger.info("启动机器人端...")

        robot_id = f"robot-{uuid.uuid4().hex[:8]}"
        session = ZenohSession(node_id=robot_id, node_type="robot")
        if not session.connect():
            logger.error("无法连接到 Zenoh 网络")
            sys.exit(1)

        device_mgr = DeviceManager(session)
        device_mgr.register_self(f"机器人 {robot_id}", "robot")
        device_mgr.start()

        def command_handler(msg: Message) -> Message:
            logger.info(f"收到指令: {msg.payload}")
            return Message(
                msg_type=MessageType.DATA,
                source_id=robot_id,
                payload={"status": "success", "result": "Command executed"},
                timestamp=time.time()
            )

        session.declare_queryable(f"smilex/device/{robot_id}/command", command_handler)

        logger.info(f"机器人端已启动 (ID: {robot_id})，按 Ctrl+C 停止")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            device_mgr.stop()
            session.disconnect()
            logger.info("机器人端已停止")

    except Exception as e:
        logger.error(f"运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
