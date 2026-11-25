from typing import Required, TypedDict

from langchain_core.documents import Document


class IngestionState(TypedDict, total=False):
    """导入流程图状态"""

    task_id: str

    document_id: str

    file_path: Required[str]

    # ===== 文件信息 =====

    file_title: str

    item_name: str

    # ===== 中间数据 =====

    markdown_content: str

    chunks: list[Document]

    # ===== 向量化结果 =====

    item_name_dense_embedding: list[float]

    item_name_sparse_embedding: dict[int, float]

    chunk_dense_embeddings: list[list[float]]

    chunk_sparse_embeddings: list[dict[int, float]]
