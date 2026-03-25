"""
云端控制器主模块
"""

import sys
import time

from common.config.settings import settings
from common.utils.logger import logger
from common.core import ZenohSession, DeviceManager


def main():
    """
    主函数
    """
    logger.info(f"启动 SmileX Zenoh Gateway - 云端控制器 v{settings.app_version}")

    try:
        logger.info("启动云端控制器...")

        session = ZenohSession(node_id="cloud-controller", node_type="cloud")
        if not session.connect():
            logger.error("无法连接到 Zenoh 网络")
            sys.exit(1)

        device_mgr = DeviceManager(session)
        device_mgr.register_self("云端控制平台", "cloud")
        device_mgr.start()

        logger.info("云端控制器已启动，按 Ctrl+C 停止")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            device_mgr.stop()
            session.disconnect()
            logger.info("云端控制器已停止")

    except Exception as e:
        logger.error(f"运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
