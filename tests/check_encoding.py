"""
检查 Zenoh Encoding API
"""

import zenoh

print("检查 Encoding:")
print(dir(zenoh.Encoding))

print("\n检查 APPLICATION_JSON:")
print(zenoh.Encoding.APPLICATION_JSON)
print(f"类型: {type(zenoh.Encoding.APPLICATION_JSON)}")
