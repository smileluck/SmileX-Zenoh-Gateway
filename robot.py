"""
机器人端启动脚本
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from robot.__main__ import main

if __name__ == "__main__":
    main()
