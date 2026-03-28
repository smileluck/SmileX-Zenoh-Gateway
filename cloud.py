import sys
import os
import time
import cv2
import numpy as np
import zenoh
from logging import getLogger
import queue
import threading
import struct

from common.setup import setup_logging
setup_logging()

logger = getLogger(__name__)

# 当前秒
current_second = None
frame_index = 0
current_batch_num = -1
output_dir = "output"

def get_time_folder():
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())



q = queue.Queue(maxsize=50)

def listener(sample):
    # logger.info(sample.payload)
    try:
        q.put_nowait(sample)
    except queue.Full:
        logger.info("队列已满，丢帧")
        pass


def worker():
    global current_second, frame_index, current_batch_num
    logger.info("线程启动")
    while True:
        # logger.info(f"q size: {q.qsize()}")
        sample = q.get()
        data = sample.payload.to_bytes()

        # 解析头
        ts, batch_num = struct.unpack("dI", data[:12])

        # logger.info(f"batch_num={batch_num}, 延迟={time.time()-ts:.3f}s")

        # 图片数据
        img_bytes = data[12:]

        now_sec = int(time.time())

        # 新的一秒 → 新建目录
        # if current_second != now_sec:
            # current_second = now_sec
            # frame_index = 0

            # folder = os.path.join(output_dir, get_time_folder())
            # os.makedirs(folder, exist_ok=True)

            # logger.info(f"新时间片目录: {folder}")

        # 新的批次 → 新建目录
        if current_batch_num != batch_num:
            logger.info(f"原先批次: {current_batch_num},帧索引: {frame_index}")
            current_batch_num = batch_num

            

            frame_index = 0
            
            folder = os.path.join(output_dir, f"batch_{batch_num:04d}")
            os.makedirs(folder, exist_ok=True)

            # logger.info(f"新批次目录: {folder}")

            # folder = os.path.join(output_dir, get_time_folder())
            # os.makedirs(folder, exist_ok=True)

            # logger.info(f"新批次目录: {folder}")



        # 当前目录
        # folder = os.path.join(output_dir, f"batch_{batch_num:04d}")
        
        # np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        # frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # if frame is None:
        #     return

        # # 保存
        # filename = os.path.join(folder, f"frame_{frame_index:04d}.jpg")
        # cv2.imwrite(filename, frame)

        frame_index += 1

NUM_WORKERS = 1  # 根据CPU核数调

def start_workers():
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        logger.info(f"worker-{i} 启动")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, "config", "zenoh_config_cloud.json")
    config_path = os.environ.get("ZENOH_CONFIG_PATH", default_config_path)

    if not os.path.exists(config_path):
        logger.info(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    config = zenoh.Config.from_file(config_path)
    session = zenoh.open(config)

    logger.info("云端控制器已启动")

    session.declare_subscriber("robot/camera/frame", listener)

    start_workers()
    try:
        while True:
            # time.sleep(1)
            pass
    except KeyboardInterrupt:
        pass
    finally:
        session.close()
        logger.info("Zenoh 会话已关闭")
        sys.exit(0)


if __name__ == "__main__":
    main()