"""
测试安全模块
"""

import time

from smilex_zenoh_gateway.security import (
    CryptoManager,
    EncryptedData,
    AuthManager,
    TokenInfo,
    TokenType
)
from logging import getLogger

logger = getLogger(__name__)


def test_crypto():
    """测试加密解密功能"""
    logger.info("=" * 50)
    logger.info("测试加密解密功能")
    
    crypto = CryptoManager()
    
    test_data = {
        "message": "Hello, World!",
        "number": 42,
        "nested": {"key": "value"}
    }
    
    encrypted = crypto.encrypt(test_data)
    logger.info(f"加密成功: nonce={encrypted.nonce[:20]}...")
    
    decrypted = crypto.decrypt(encrypted)
    logger.info(f"解密成功: {decrypted}")
    
    assert decrypted == test_data, "解密后的数据应该与原数据一致"
    
    encrypted_dict = crypto.encrypt_to_dict(test_data)
    decrypted_from_dict = crypto.decrypt_from_dict(encrypted_dict)
    assert decrypted_from_dict == test_data, "字典格式加密解密应该一致"
    
    key_b64 = crypto.get_key_b64()
    crypto2 = CryptoManager.from_key_b64(key_b64)
    decrypted2 = crypto2.decrypt(encrypted)
    assert decrypted2 == test_data, "从密钥恢复的加密管理器应该能解密"
    
    logger.info("✓ 加密解密测试通过")


def test_auth():
    """测试认证功能"""
    logger.info("=" * 50)
    logger.info("测试认证功能")
    
    auth = AuthManager()
    
    device_id = "robot-001"
    valid_secrets = {
        "robot-001": "secret123",
        "robot-002": "secret456"
    }
    
    access_token = auth.generate_token(device_id, TokenType.ACCESS)
    logger.info(f"生成访问令牌成功: {access_token.token[:30]}...")
    
    verified = auth.verify_token(access_token.token)
    assert verified is not None, "令牌验证应该成功"
    assert verified.device_id == device_id, "设备ID应该一致"
    logger.info("✓ 令牌验证成功")
    
    refresh_token = auth.generate_token(device_id, TokenType.REFRESH)
    logger.info(f"生成刷新令牌成功: {refresh_token.token[:30]}...")
    
    new_access = auth.refresh_token(refresh_token.token)
    assert new_access is not None, "刷新令牌应该成功"
    assert new_access.device_id == device_id, "刷新后的设备ID应该一致"
    logger.info("✓ 令牌刷新成功")
    
    auth_result = auth.authenticate_device("robot-001", "secret123", valid_secrets)
    assert auth_result is not None, "认证应该成功"
    logger.info("✓ 设备认证成功")
    
    auth_fail = auth.authenticate_device("robot-001", "wrongsecret", valid_secrets)
    assert auth_fail is None, "错误密钥认证应该失败"
    logger.info("✓ 错误密钥认证失败（预期）")
    
    revoked = auth.revoke_token(new_access.token)
    assert revoked, "撤销令牌应该成功"
    assert auth.verify_token(new_access.token) is None, "撤销后的令牌应该验证失败"
    logger.info("✓ 令牌撤销成功")
    
    logger.info("✓ 认证功能测试通过")


def main():
    """运行所有测试"""
    logger.info("开始安全模块测试")
    try:
        test_crypto()
        test_auth()
        logger.info("\n所有测试通过！✓")
    except Exception as e:
        logger.error(f"\n测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
