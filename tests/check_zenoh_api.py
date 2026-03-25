"""
检查 Zenoh 库 API
"""

import zenoh

print("Zenoh 模块内容:")
print(dir(zenoh))

print("\n尝试查找 open 函数:")
if hasattr(zenoh, 'open'):
    print("找到 open 函数")
    print(f"open 函数类型: {type(zenoh.open)}")
    
if hasattr(zenoh, 'Session'):
    print("\n找到 Session 类")
    print(f"Session 类: {zenoh.Session}")

print("\nZenoh 版本信息:")
try:
    print(zenoh.__version__)
except AttributeError:
    print("没有 __version__ 属性")
