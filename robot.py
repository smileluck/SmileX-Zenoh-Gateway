import sys
import os
import time
import cv2
import zenoh
from logging import getLogger
import struct

from common.setup import setup_logging
setup_logging()

logger = getLogger(__name__)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, "config", "zenoh_config_robot.json")
    config_path = os.environ.get("ZENOH_CONFIG_PATH", default_config_path)

    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    config = zenoh.Config.from_file(config_path)

    TARGET_FPS = 40.0
    interval = 1.0 / TARGET_FPS

    session = zenoh.open(config)
    pub = session.declare_publisher(
        "robot/camera/frame",
        reliability=zenoh.Reliability.BEST_EFFORT,
        # congestion_control=zenoh.CongestionControl.DROP
    )

    # 图片加载
    img = cv2.imread("test.jpg")
    _, img_encoded = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    data = img_encoded.tobytes()

    print(f"单帧大小: {len(data)/1024:.2f} KB")

    # 统计
    batch_num = 0
    count = 0
    last_stat_time = time.perf_counter()

    # 帧率控制
    next_time = time.perf_counter()

    try:
        while True:
            now = time.perf_counter()

            # 控制帧率
            if now < next_time:
                # logger.info(f"等待 {next_time - now:.2f} 秒")
                time.sleep(next_time - now)


            send_time = time.time()  # 用于延迟计算（秒级时间戳）

            # ✅ 打包：时间戳(double) + frame_id(uint32)
            header = struct.pack("dI", send_time, batch_num)

            packet = header + data
            # 发送
            pub.put(packet) 
            # pub.put(str(count))
            count += 1

            # 更新下一帧时间
            next_time += interval

            # 防止累积漂移（关键优化）
            if now - next_time > 1:
                logger.info("时间漂移，重置下一帧时间")
                next_time = now

            # 每秒统计一次
            if now - last_stat_time >= 1.0:
                elapsed = now - last_stat_time
                fps = count / elapsed
                bandwidth = (len(data) * count) / elapsed / 1024 / 1024

                logger.info(f"FPS: {fps:.2f}, 带宽: {bandwidth:.2f} MB/s,count={count}")

                count = 0
                batch_num+=1
                # time.sleep(1)
                last_stat_time = time.perf_counter()
                

    except KeyboardInterrupt:
        pass
    finally:
        session.close()
        logger.info("Zenoh 会话已关闭")
        sys.exit(0)

if __name__ == "__main__":
    main()