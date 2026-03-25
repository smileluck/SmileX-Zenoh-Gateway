"""
检查 Zenoh Session API
"""

import zenoh

print("创建 Session...")
session = zenoh.open()

print("\nSession 方法:")
print([method for method in dir(session) if not method.startswith('_')])

print("\n尝试关闭 Session...")
session.close()
print("Session 已关闭")
