import logging
from typing import Any

from core.exceptions import EmbeddingError, StateFieldError
from core.graphs.ingestion.state import IngestionState
from infrastructure.models.embedding import embed_func

logger = logging.getLogger(__name__)


def embed_document(state: IngestionState) -> dict[str, Any]:
    """向量化产品名和所有文档块"""
    _validate_state(state)

    # 合并产品名和文档块
    item_name = state["item_name"]
    chunks = state["chunks"]
    docs = [item_name, *(chunk.page_content for chunk in chunks)]

    try:
        # 向量化
        result = embed_func.encode_documents(docs)
        dense_vectors = result.get("dense")
        sparse_matrix = result.get("sparse")

        if dense_vectors is None or sparse_matrix is None:
            raise EmbeddingError(
                "BGE-M3 未同时返回 dense 和 sparse 向量",
                node_name="embed_document",
            )

        dense_embeddings = [
            [float(value) for value in vector]
            for vector in dense_vectors
        ]
        sparse_embeddings = _sparse_rows_to_dicts(sparse_matrix.tocsr())
    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(
            f"BGE-M3 产品名或文档向量化失败: {e}",
            node_name="embed_document",
        ) from e

    return {
        "item_name_dense_embedding": dense_embeddings[0],
        "item_name_sparse_embedding": sparse_embeddings[0],
        "chunk_dense_embeddings": dense_embeddings[1:],
        "chunk_sparse_embeddings": sparse_embeddings[1:],
    }


def _validate_state(state: IngestionState) -> None:
    """校验状态"""
    item_name = state.get("item_name")
    if not isinstance(item_name, str) or not item_name.strip():
        raise StateFieldError(
            node_name="embed_document",
            field_name="item_name",
            message="产品名称不能为空",
        )

    chunks = state.get("chunks")
    if not chunks or not isinstance(chunks, list):
        raise StateFieldError(
            node_name="embed_document",
            field_name="chunks",
            message="文档块不能为空",
            expected_type=list,
        )

    for index, chunk in enumerate(chunks):
        content = getattr(chunk, "page_content", None)
        if not isinstance(content, str) or not content.strip():
            raise StateFieldError(
                node_name="embed_document",
                field_name=f"chunks[{index}].page_content",
                message="文档块内容不能为空",
            )


def _sparse_rows_to_dicts(sparse_matrix: Any) -> list[dict[int, float]]:
    """将 BGE-M3 的稀疏矩阵按行转换为 Milvus 可用的 token 权重字典"""
    sparse_csr = sparse_matrix.tocsr()
    rows: list[dict[int, float]] = []

    for row in range(sparse_csr.shape[0]):
        start = sparse_csr.indptr[row]
        end = sparse_csr.indptr[row + 1]
        rows.append({
            int(token_id): float(weight)
            for token_id, weight in zip(
                sparse_csr.indices[start:end],
                sparse_csr.data[start:end],
                strict=True,
            )
        })

    return rows
