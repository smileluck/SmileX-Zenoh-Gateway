"""
配置管理模块
使用 pydantic-settings 进行配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    """
    
    # 应用基本配置
    app_name: str = "SmileX Zenoh Gateway"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # Zenoh 配置
    zenoh_connect: Optional[str] = None
    zenoh_listen: Optional[str] = "tcp/0.0.0.0:7447"
    
    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 设备配置
    heartbeat_interval: float = 1.0  # 心跳间隔（秒）
    heartbeat_timeout: float = 3.0  # 心跳超时（秒）
    max_devices: int = 50  # 最大设备数
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # 安全配置
    enable_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_cert_path: Optional[str] = None
    
    # 加密密钥配置
    encryption_key: Optional[str] = None
    token_secret: Optional[str] = None
    
    class Config:
        env_prefix = "SMILEX_"
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()
