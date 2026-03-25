"""
日志工具模块
提供结构化日志功能
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path

from ..config.settings import settings


def setup_logger(
    name: str = "smilex_zenoh_gateway",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_max_bytes: Optional[int] = None,
    log_backup_count: Optional[int] = None,
) -> logging.Logger:
    """
    设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_file: 日志文件路径
        log_max_bytes: 单个日志文件最大字节数
        log_backup_count: 保留的日志文件数量
    
    Returns:
        配置好的日志记录器
    """
    # 使用配置文件中的默认值
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    log_max_bytes = log_max_bytes or settings.log_max_bytes
    log_backup_count = log_backup_count or settings.log_backup_count
    
    # 获取或创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果配置了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger


# 获取全局日志记录器
logger = setup_logger()
