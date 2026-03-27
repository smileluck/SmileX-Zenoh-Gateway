import sys
import os
import time
import cv2
import numpy as np
import zenoh
from logging import getLogger

from common.setup import setup_logging
setup_logging()

logger = getLogger(__name__)

# 当前秒
current_second = None
frame_index = 0
output_dir = "output"

def get_time_folder():
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())


def listener(sample):
    global current_second, frame_index

    now_sec = int(time.time())

    # 新的一秒 → 新建目录
    if current_second != now_sec:
        current_second = now_sec
        frame_index = 0

        folder = os.path.join(output_dir, get_time_folder())
        os.makedirs(folder, exist_ok=True)

        logger.info(f"新时间片目录: {folder}")

    # 当前目录
    folder = os.path.join(output_dir, get_time_folder())

    # 解码图片
    data = sample.payload.to_bytes()

    
    np_arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return

    # 保存
    filename = os.path.join(folder, f"frame_{frame_index:04d}.jpg")
    cv2.imwrite(filename, frame)

    frame_index += 1


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, "config", "zenoh_config_cloud.json")
    config_path = os.environ.get("ZENOH_CONFIG_PATH", default_config_path)

    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    config = zenoh.Config.from_file(config_path)
    session = zenoh.open(config)

    logger.info("云端控制器已启动")

    session.declare_subscriber("robot/camera/frame", listener)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        session.close()
        logger.info("Zenoh 会话已关闭")
        sys.exit(0)


if __name__ == "__main__":
    main()