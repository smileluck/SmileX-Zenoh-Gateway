"""
API 服务入口
"""

import sys
from api.main import run_server


def main():
    """
    主函数
    """
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"运行出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
