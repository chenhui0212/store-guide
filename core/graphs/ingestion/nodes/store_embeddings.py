import logging
from _sha2 import sha256

from core.exceptions import StorageError, StateFieldError
from core.graphs.ingestion.state import IngestionState
from infrastructure.storage.milvus_embedding_store import get_embedding_store_client

logger = logging.getLogger(__name__)


def store_embeddings(state: IngestionState):
    """写入向量数据库"""
    _validate_state(state)

    try:
        document_id = _get_document_id(state)
        client = get_embedding_store_client()
        client.upsert_item_name(
            document_id=document_id,
            file_title=state["file_title"],
            item_name=state["item_name"],
            dense_vector=state["item_name_dense_embedding"],
            sparse_vector=state["item_name_sparse_embedding"],
        )
        client.upsert_chunks(
            document_id=document_id,
            file_title=state["file_title"],
            item_name=state["item_name"],
            chunks=state["chunks"],
            dense_vectors=state["chunk_dense_embeddings"],
            sparse_vectors=state["chunk_sparse_embeddings"],
        )
    except Exception as e:
        raise StorageError(
            f"写入产品名或文档块到向量数据库失败: {e}",
            node_name="store_embeddings",
        ) from e
    logger.info("写入向量数据库完成")


def _validate_state(state: IngestionState) -> None:
    """校验状态"""
    item_name = state.get("item_name")
    if not isinstance(item_name, str) or not item_name.strip():
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="item_name",
            message="item_name 不能为空",
        )

    chunks = state.get("chunks")
    dense_vectors = state.get("chunk_dense_embeddings")
    sparse_vectors = state.get("chunk_sparse_embeddings")
    item_dense = state.get("item_name_dense_embedding")
    item_sparse = state.get("item_name_sparse_embedding")

    if not isinstance(chunks, list) or not chunks:
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="chunks",
            expected_type=list,
            message="文档块不能为空",
        )
    if not isinstance(dense_vectors, list) or len(dense_vectors) != len(chunks):
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="chunk_dense_embeddings",
            expected_type=list,
            message="文档块与 dense 向量数量不一致",
        )
    if not isinstance(sparse_vectors, list) or len(sparse_vectors) != len(chunks):
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="chunk_sparse_embeddings",
            expected_type=list,
            message="文档块与 sparse 向量数量不一致",
        )
    if not isinstance(item_dense, list) or not item_dense:
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="item_name_dense_embedding",
            expected_type=list,
            message="产品名 dense 向量不能为空",
        )
    if not isinstance(item_sparse, dict) or not item_sparse:
        raise StateFieldError(
            node_name="store_embeddings",
            field_name="item_name_sparse_embedding",
            expected_type=dict,
            message="产品名 sparse 向量不能为空",
        )


def _get_document_id(state: IngestionState) -> str:
    # 优先使用调用方的文档编号，否则以文件名生成
    document_id = state.get("document_id")
    if document_id:
        return document_id
    return sha256(state["file_title"].encode("utf-8")).hexdigest()
