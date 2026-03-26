"""
设备认证模块
负责设备认证和令牌管理
"""

import time
import hmac
import hashlib
import secrets
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from common.config.settings import settings
from logging import getLogger

logger = getLogger(__name__)


class TokenType(Enum):
    """
    令牌类型枚举
    """
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenInfo:
    """
    令牌信息数据类
    """
    token: str
    token_type: TokenType
    device_id: str
    issued_at: float
    expires_at: float
    metadata: Dict[str, Any]


class AuthManager:
    """
    认证管理器类
    负责设备认证、令牌生成和验证
    """

    # 默认令牌有效期（秒）
    DEFAULT_ACCESS_TOKEN_EXPIRE = 3600  # 1小时
    DEFAULT_REFRESH_TOKEN_EXPIRE = 86400 * 7  # 7天

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化认证管理器
        
        Args:
            secret_key: 密钥，如果为 None 则从配置读取或自动生成
        """
        if secret_key is None and settings.token_secret:
            secret_key = settings.token_secret
            logger.info("从配置加载令牌密钥")
        
        self._secret_key = secret_key or self._generate_secret_key()
        self._tokens: Dict[str, TokenInfo] = {}
        
        logger.info("初始化认证管理器")

    @staticmethod
    def _generate_secret_key() -> str:
        """
        生成随机密钥
        
        Returns:
            随机密钥字符串
        """
        return secrets.token_urlsafe(64)

    def generate_token(
        self,
        device_id: str,
        token_type: TokenType = TokenType.ACCESS,
        expire_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenInfo:
        """
        生成令牌
        
        Args:
            device_id: 设备ID
            token_type: 令牌类型
            expire_seconds: 过期时间（秒）
            metadata: 附加元数据
        
        Returns:
            令牌信息
        """
        if expire_seconds is None:
            if token_type == TokenType.ACCESS:
                expire_seconds = self.DEFAULT_ACCESS_TOKEN_EXPIRE
            else:
                expire_seconds = self.DEFAULT_REFRESH_TOKEN_EXPIRE
        
        issued_at = time.time()
        expires_at = issued_at + expire_seconds
        
        token_data = {
            "device_id": device_id,
            "token_type": token_type.value,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "metadata": metadata or {}
        }
        
        token = self._sign_token(token_data)
        
        token_info = TokenInfo(
            token=token,
            token_type=token_type,
            device_id=device_id,
            issued_at=issued_at,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self._tokens[token] = token_info
        
        logger.info(f"生成令牌成功: device_id={device_id}, type={token_type.value}")
        return token_info

    def _sign_token(self, data: Dict[str, Any]) -> str:
        """
        签名令牌数据
        
        Args:
            data: 令牌数据
        
        Returns:
            签名后的令牌
        """
        import json
        
        data_json = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self._secret_key.encode("utf-8"),
            data_json.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        token_data = {
            "data": data,
            "signature": signature
        }
        
        token_json = json.dumps(token_data)
        return base64.urlsafe_b64encode(token_json.encode("utf-8")).decode("utf-8").rstrip("=")

    def verify_token(self, token: str) -> Optional[TokenInfo]:
        """
        验证令牌
        
        Args:
            token: 要验证的令牌
        
        Returns:
            令牌信息，如果验证失败返回 None
        """
        try:
            token_info = self._parse_token(token)
            
            if token_info is None:
                return None
            
            if time.time() > token_info.expires_at:
                logger.warning(f"令牌已过期: {token_info.device_id}")
                return None
            
            if token not in self._tokens:
                logger.warning(f"令牌不存在: {token_info.device_id}")
                return None
            
            logger.debug(f"令牌验证成功: {token_info.device_id}")
            return token_info
            
        except Exception as e:
            logger.error(f"令牌验证失败: {e}", exc_info=True)
            return None

    def _parse_token(self, token: str) -> Optional[TokenInfo]:
        """
        解析令牌
        
        Args:
            token: 令牌字符串
        
        Returns:
            令牌信息，解析失败返回 None
        """
        import json
        
        try:
            padding = 4 - len(token) % 4
            if padding != 4:
                token += "=" * padding
            
            token_json = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            token_data = json.loads(token_json)
            
            data = token_data["data"]
            signature = token_data["signature"]
            
            expected_signature = hmac.new(
                self._secret_key.encode("utf-8"),
                json.dumps(data, sort_keys=True).encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("令牌签名验证失败")
                return None
            
            return TokenInfo(
                token=token,
                token_type=TokenType(data["token_type"]),
                device_id=data["device_id"],
                issued_at=data["issued_at"],
                expires_at=data["expires_at"],
                metadata=data.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"解析令牌失败: {e}", exc_info=True)
            return None

    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌
        
        Args:
            token: 要撤销的令牌
        
        Returns:
            是否撤销成功
        """
        if token in self._tokens:
            del self._tokens[token]
            logger.info(f"令牌已撤销")
            return True
        return False

    def revoke_all_tokens(self, device_id: str) -> int:
        """
        撤销设备的所有令牌
        
        Args:
            device_id: 设备ID
        
        Returns:
            撤销的令牌数量
        """
        revoked_count = 0
        tokens_to_revoke = [
            token for token, info in self._tokens.items()
            if info.device_id == device_id
        ]
        
        for token in tokens_to_revoke:
            del self._tokens[token]
            revoked_count += 1
        
        logger.info(f"撤销设备 {device_id} 的 {revoked_count} 个令牌")
        return revoked_count

    def refresh_token(self, refresh_token: str) -> Optional[TokenInfo]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的访问令牌信息，失败返回 None
        """
        token_info = self.verify_token(refresh_token)
        
        if token_info is None:
            return None
        
        if token_info.token_type != TokenType.REFRESH:
            logger.warning("需要刷新令牌")
            return None
        
        self.revoke_token(refresh_token)
        
        new_access_token = self.generate_token(
            device_id=token_info.device_id,
            token_type=TokenType.ACCESS,
            metadata=token_info.metadata
        )
        
        logger.info(f"令牌刷新成功: {token_info.device_id}")
        return new_access_token

    def authenticate_device(
        self,
        device_id: str,
        device_secret: str,
        valid_secrets: Dict[str, str]
    ) -> Optional[TokenInfo]:
        """
        设备认证
        
        Args:
            device_id: 设备ID
            device_secret: 设备密钥
            valid_secrets: 有效的设备密钥字典
        
        Returns:
            访问令牌信息，认证失败返回 None
        """
        if device_id not in valid_secrets:
            logger.warning(f"设备认证失败: 未知设备 {device_id}")
            return None
        
        expected_secret = valid_secrets[device_id]
        
        if not hmac.compare_digest(device_secret, expected_secret):
            logger.warning(f"设备认证失败: 密钥错误 {device_id}")
            return None
        
        access_token = self.generate_token(
            device_id=device_id,
            token_type=TokenType.ACCESS
        )
        
        logger.info(f"设备认证成功: {device_id}")
        return access_token

    def get_secret_key_b64(self) -> str:
        """
        获取 Base64 编码的密钥
        
        Returns:
            Base64 编码的密钥
        """
        return base64.urlsafe_b64encode(self._secret_key.encode("utf-8")).decode("utf-8")

    @classmethod
    def from_secret_key_b64(cls, secret_key_b64: str) -> "AuthManager":
        """
        从 Base64 编码的密钥创建认证管理器
        
        Args:
            secret_key_b64: Base64 编码的密钥
        
        Returns:
            认证管理器实例
        """
        secret_key = base64.urlsafe_b64decode(secret_key_b64.encode("utf-8")).decode("utf-8")
        return cls(secret_key=secret_key)
