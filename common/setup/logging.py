"""
日志工具模块
提供结构化日志功能
"""
import logging
import logging.config
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # 保留第三方logger

    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        },
        "json": {
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
        },
    },

    "handlers": {
        # 控制台输出
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },

        # 普通日志（滚动）
        "file_info": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": f"{LOG_DIR}/app.log",
            "when": "midnight",
            "backupCount": 7,
            "encoding": "utf-8"
        },

        # 错误日志单独输出
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "standard",
            "filename": f"{LOG_DIR}/error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8"
        },
    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "file_info", "file_error"]
    },

    # 针对特定模块（可选）
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)