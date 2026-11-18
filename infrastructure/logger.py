"""全局日志配置"""
from __future__ import annotations

import os
from logging.config import dictConfig


def setup_logging(level: str | None = None) -> None:
    """初始化全局日志，应在应用入口调用一次。

    级别可通过参数或 LOG_LEVEL 环境变量覆盖，默认 INFO。
    """
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": (level or os.getenv("LOG_LEVEL", "INFO")).upper(),
            "handlers": ["console"],
        },
    })
