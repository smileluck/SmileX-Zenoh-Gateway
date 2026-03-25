"""
简单的 Zenoh 测试
"""

import zenoh
import json
import time

print("测试 1: 创建 Config")
try:
    config = zenoh.Config()
    print("✓ Config 创建成功")
    print(f"Config 对象: {config}")
except Exception as e:
    print(f"✗ Config 创建失败: {e}")

print("\n测试 2: 使用默认配置打开 Session")
try:
    session = zenoh.open(zenoh.Config())
    print("✓ Session 打开成功")
    print(f"Session 对象: {session}")
    
    print("\n测试 3: 检查 Session 方法")
    print("Session 公有方法:")
    for attr in dir(session):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    print("\n测试 4: 关闭 Session")
    session.close()
    print("✓ Session 已关闭")
    
except Exception as e:
    print(f"✗ Session 操作失败: {e}")
    import traceback
    traceback.print_exc()
