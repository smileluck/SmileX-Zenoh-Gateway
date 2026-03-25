"""
安全密钥生成工具
用于生成 SmileX Zenoh Gateway 的加密密钥和令牌签名密钥
"""

import secrets
import base64


def generate_encryption_key() -> str:
    """
    生成 AES-256-GCM 加密密钥（Base64 编码）
    
    Returns:
        Base64 编码的 32 字节密钥
    """
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode("utf-8")


def generate_token_secret() -> str:
    """
    生成令牌签名密钥
    
    Returns:
        安全的随机字符串密钥
    """
    return secrets.token_hex(32)


def main():
    print("=" * 60)
    print("SmileX Zenoh Gateway - 安全密钥生成工具")
    print("=" * 60)
    print()
    
    encryption_key = generate_encryption_key()
    token_secret = generate_token_secret()
    
    print("🔐 生成的安全密钥：")
    print()
    print("加密密钥 (用于 AES-256-GCM):")
    print(f"SMILEX_ENCRYPTION_KEY={encryption_key}")
    print()
    print("令牌密钥 (用于 HMAC-SHA256 签名):")
    print(f"SMILEX_TOKEN_SECRET={token_secret}")
    print()
    print("=" * 60)
    print("⚠️  重要提示：")
    print("1. 请将以上密钥添加到你的 .env 文件中")
    print("2. 请妥善保管这些密钥，不要泄露")
    print("3. 生产环境请使用不同的密钥")
    print("=" * 60)


if __name__ == "__main__":
    main()
