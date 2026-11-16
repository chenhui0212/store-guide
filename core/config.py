"""配置中心
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 加载配置文件
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _int(key: str, default: int) -> int:
    """从环境读整数"""
    return int(os.getenv(key, str(default)))


def _csv(key: str, default: str = "") -> tuple[str, ...]:
    """读取逗号分隔的环境变量"""
    return tuple(
        item.strip()
        for item in os.getenv(key, default).split(",")
        if item.strip()
    )


def _size(key: str, default: str) -> int:
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"缺少配置项：{key}")

    match = re.fullmatch(r"\s*(\d+)\s*(B|KB|MB|GB)?\s*", value, re.IGNORECASE)
    if not match:
        raise ValueError(f"{key} 格式无效：{value!r}，示例：10MB")

    number = int(match.group(1))
    unit = (match.group(2) or "B").upper()
    multiplier = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[unit]
    return number * multiplier


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek-v4-pro")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据层连接
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Milvus
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "store-guide")

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j-dev")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "store-guide")

# PostgreSQL
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/store-guide")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 业务参数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 文本处理参数
SUPPORTED_EXTENSIONS = frozenset(
    f".{item.lower().lstrip('.')}"
    for item in _csv("SUPPORTED_EXTENSIONS", ".pdf,.docx")
)
MAX_FILE_SIZE = _size("MAX_FILE_SIZE", "10MB")
MAX_CONTENT_LENGTH = _int("MAX_CONTENT_LENGTH", 10000)
