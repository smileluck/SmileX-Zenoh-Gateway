"""
测试模块导入
"""

def test_import_config():
    """测试配置模块导入"""
    from smilex_zenoh_gateway.config.settings import settings
    assert settings is not None
    print("✓ 配置模块导入成功")

def test_import_logger():
    """测试日志模块导入"""
    from smilex_zenoh_gateway.utils.logger import logger
    assert logger is not None
    print("✓ 日志模块导入成功")

def test_import_version():
    """测试版本导入"""
    from smilex_zenoh_gateway import __version__
    assert __version__ == "0.1.0"
    print("✓ 版本模块导入成功")

if __name__ == "__main__":
    test_import_config()
    test_import_logger()
    test_import_version()
    print("\n所有导入测试通过！✓")
