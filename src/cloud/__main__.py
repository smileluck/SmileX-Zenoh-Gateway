"""
云端控制器入口
"""

import sys
from cloud.main import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"运行出错: {e}", file=sys.stderr)
        sys.exit(1)
