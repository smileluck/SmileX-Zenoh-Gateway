"""
加密解密模块
提供数据加密解密功能
"""

import os
import base64
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from common.config.settings import settings
from common.utils.logger import logger


@dataclass
class EncryptedData:
    """
    加密数据结构
    """
    ciphertext: str
    nonce: str
    tag: str


class CryptoManager:
    """
    加密管理器类
    负责数据加密、解密和密钥管理
    """

    # AES-GCM 参数
    NONCE_LENGTH = 12  # 96位
    KEY_LENGTH = 32  # 256位
    SALT_LENGTH = 16

    def __init__(self, key: Optional[bytes] = None):
        """
        初始化加密管理器
        
        Args:
            key: 加密密钥，如果为 None 则从配置读取或自动生成
        """
        if key is None and settings.encryption_key:
            try:
                key = base64.b64decode(settings.encryption_key)
                logger.info("从配置加载加密密钥")
            except Exception as e:
                logger.warning(f"从配置加载加密密钥失败: {e}，使用自动生成的密钥")
                key = None
        
        self._key = key or self.generate_key()
        self._aesgcm = AESGCM(self._key)
        
        logger.info("初始化加密管理器")

    @staticmethod
    def generate_key() -> bytes:
        """
        生成随机密钥
        
        Returns:
            32字节的随机密钥
        """
        return os.urandom(CryptoManager.KEY_LENGTH)

    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        从密码派生密钥
        
        Args:
            password: 密码字符串
            salt: 盐值，如果为 None 则自动生成
        
        Returns:
            (密钥, 盐值)
        """
        if salt is None:
            salt = os.urandom(CryptoManager.SALT_LENGTH)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=CryptoManager.KEY_LENGTH,
            salt=salt,
            iterations=480000,
        )
        
        key = kdf.derive(password.encode("utf-8"))
        return key, salt

    def encrypt(self, data: Dict[str, Any]) -> EncryptedData:
        """
        加密数据
        
        Args:
            data: 要加密的数据字典
        
        Returns:
            加密后的数据
        """
        try:
            json_data = json.dumps(data).encode("utf-8")
            nonce = os.urandom(self.NONCE_LENGTH)
            
            encrypted = self._aesgcm.encrypt(nonce, json_data, associated_data=None)
            
            ciphertext = encrypted[:-16]
            tag = encrypted[-16:]
            
            result = EncryptedData(
                ciphertext=base64.b64encode(ciphertext).decode("utf-8"),
                nonce=base64.b64encode(nonce).decode("utf-8"),
                tag=base64.b64encode(tag).decode("utf-8")
            )
            
            logger.debug("数据加密成功")
            return result
            
        except Exception as e:
            logger.error(f"数据加密失败: {e}", exc_info=True)
            raise

    def decrypt(self, encrypted_data: EncryptedData) -> Dict[str, Any]:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据
        
        Returns:
            解密后的数据字典
        """
        try:
            nonce = base64.b64decode(encrypted_data.nonce)
            ciphertext = base64.b64decode(encrypted_data.ciphertext)
            tag = base64.b64decode(encrypted_data.tag)
            
            encrypted = ciphertext + tag
            
            json_data = self._aesgcm.decrypt(nonce, encrypted, associated_data=None)
            data = json.loads(json_data.decode("utf-8"))
            
            logger.debug("数据解密成功")
            return data
            
        except Exception as e:
            logger.error(f"数据解密失败: {e}", exc_info=True)
            raise

    def encrypt_to_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        加密数据并转换为字典格式
        
        Args:
            data: 要加密的数据
        
        Returns:
            加密后的字典
        """
        encrypted = self.encrypt(data)
        return {
            "ciphertext": encrypted.ciphertext,
            "nonce": encrypted.nonce,
            "tag": encrypted.tag
        }

    def decrypt_from_dict(self, encrypted_dict: Dict[str, str]) -> Dict[str, Any]:
        """
        从字典格式解密数据
        
        Args:
            encrypted_dict: 加密的字典
        
        Returns:
            解密后的数据
        """
        encrypted = EncryptedData(
            ciphertext=encrypted_dict["ciphertext"],
            nonce=encrypted_dict["nonce"],
            tag=encrypted_dict["tag"]
        )
        return self.decrypt(encrypted)

    def get_key_b64(self) -> str:
        """
        获取 Base64 编码的密钥
        
        Returns:
            Base64 编码的密钥
        """
        return base64.b64encode(self._key).decode("utf-8")

    @classmethod
    def from_key_b64(cls, key_b64: str) -> "CryptoManager":
        """
        从 Base64 编码的密钥创建加密管理器
        
        Args:
            key_b64: Base64 编码的密钥
        
        Returns:
            加密管理器实例
        """
        key = base64.b64decode(key_b64)
        return cls(key=key)
