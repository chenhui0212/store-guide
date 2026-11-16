"""全局异常定义

统一错误处理，提供更清晰的错误信息。
"""
from __future__ import annotations


class AppError(Exception):
    """应用基础异常"""

    def __init__(self, message: str, *, node_name: str = ""):
        super().__init__(message)
        self.node_name = node_name

    def __str__(self) -> str:
        if self.node_name:
            return f"[{self.node_name}] {super().__str__()}"
        return super().__str__()


class ConfigurationError(AppError):
    """配置缺失或配置值无效"""


class ValidationError(AppError):
    """输入数据不符合预期"""


class StateFieldError(AppError):
    """状态中的必需字段缺失、为空或类型不符"""

    def __init__(
            self,
            field_name: str,
            *,
            node_name: str = "",
            expected_type: type | None = None,
            message: str = "",
    ):
        self.field_name = field_name
        self.expected_type = expected_type
        if not message:
            message = f"状态字段 '{field_name}' 缺失或无效"
            if expected_type:
                message += f"，期望类型: {expected_type.__name__}"
        super().__init__(message, node_name=node_name)


class ParseDocumentError(AppError):
    """解析文档错误"""


class EmbeddingError(AppError):
    """嵌入错误"""


class RerankError(AppError):
    """重排错误"""


class SearchError(AppError):
    """搜索错误"""


class LLMError(AppError):
    """LLM 调用错误：API 失败、响应解析失败"""


class StorageError(AppError):
    """外部存储错误"""


class MilvusError(StorageError):
    """Milvus 读写错误"""


class Neo4jError(StorageError):
    """Neo4j 读写错误"""


class MinioError(StorageError):
    """MinIO 读写错误"""
