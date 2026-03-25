"""
测试配置系统功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.config.zenoh_config import get_zenoh_config_manager
from common.config.settings import settings


def test_config_manager():
    """
    测试配置管理器功能
    """
    print("=" * 60)
    print("测试配置管理器")
    print("=" * 60)
    
    for node_type in ["api", "cloud", "robot"]:
        print(f"\n测试节点类型: {node_type}")
        print("-" * 40)
        
        config_mgr = get_zenoh_config_manager(node_type)
        
        config = config_mgr.load_config()
        print(f"加载配置成功: {list(config.keys())}")
        print(f"  模式: {config.get('mode')}")
        print(f"  监听端点: {config.get('listen', {}).get('endpoints')}")
        
        env_config = {
            "zenoh_connect": "tcp/192.168.1.100:7447,tcp/192.168.1.101:7447",
            "zenoh_listen": "tcp/0.0.0.0:8888"
        }
        
        merged_config = config_mgr.get_zenoh_config(env_config)
        print(f"\n合并 env 配置后:")
        print(f"  连接端点: {merged_config.get('connect', {}).get('endpoints')}")
        print(f"  监听端点: {merged_config.get('listen', {}).get('endpoints')}")
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    test_config_manager()
