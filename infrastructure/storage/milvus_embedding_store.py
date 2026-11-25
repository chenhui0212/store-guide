from __future__ import annotations

import logging
import re
from functools import lru_cache
from hashlib import sha256

from langchain_core.documents import Document
from pymilvus import DataType, MilvusClient

import core.config as config
from infrastructure.models.embedding import embed_func

logger = logging.getLogger(__name__)


class EmbeddingStoreClient:

    def __init__(self) -> None:
        dense_dimension = embed_func.dim["dense"]
        self._item_name_collection = config.MILVUS_ITEM_NAME_COLLECTION
        self._chunk_collection = config.MILVUS_CHUNK_COLLECTION
        self._client = _connect_to_database()
        self._ensure_item_name_collection(dense_dimension)
        self._ensure_chunk_collection(dense_dimension)
        self._client.load_collection(collection_name=self._item_name_collection)
        self._client.load_collection(collection_name=self._chunk_collection)

    def _ensure_item_name_collection(self, dense_dimension: int) -> None:
        if self._client.has_collection(self._item_name_collection):
            return

        schema = self._client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field(field_name="file_title", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="item_name", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dense_dimension)
        schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)

        index_params = self._client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", index_type="AUTOINDEX", metric_type="COSINE")
        index_params.add_index(field_name="sparse_vector", index_type="SPARSE_INVERTED_INDEX", metric_type="IP")

        self._client.create_collection(
            collection_name=self._item_name_collection,
            schema=schema,
            index_params=index_params,
        )
        logger.info("创建 Milvus collection: %s", self._item_name_collection)

    def _ensure_chunk_collection(self, dense_dimension: int) -> None:
        if self._client.has_collection(self._chunk_collection):
            return

        schema = self._client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="file_title", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="item_name", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="section_path", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dense_dimension)
        schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)

        index_params = self._client.prepare_index_params()
        index_params.add_index(field_name="document_id", index_type="INVERTED", index_name="document_id_inverted_index")
        index_params.add_index(field_name="item_name", index_type="INVERTED", index_name="item_name_inverted_index")
        index_params.add_index(field_name="dense_vector", index_type="AUTOINDEX", metric_type="COSINE")
        index_params.add_index(field_name="sparse_vector", index_type="SPARSE_INVERTED_INDEX", metric_type="IP")

        self._client.create_collection(
            collection_name=self._chunk_collection,
            schema=schema,
            index_params=index_params,
        )
        logger.info("创建 Milvus collection: %s", self._chunk_collection)

    def upsert_item_name(
            self,
            *,
            document_id: str,
            file_title: str,
            item_name: str,
            dense_vector: list[float],
            sparse_vector: dict[int, float],
    ) -> None:
        item_row = {
            "document_id": document_id,
            "file_title": file_title,
            "item_name": item_name,
            "dense_vector": dense_vector,
            "sparse_vector": sparse_vector,
        }
        self._client.upsert(self._item_name_collection, data=[item_row])

    def upsert_chunks(
            self,
            *,
            document_id: str,
            file_title: str,
            item_name: str,
            chunks: list[Document],
            dense_vectors: list[list[float]],
            sparse_vectors: list[dict[int, float]],
    ) -> None:
        rows = []
        for index, (chunk, dense_vector, sparse_vector) in enumerate(
                zip(chunks, dense_vectors, sparse_vectors, strict=True)
        ):
            chunk_id = sha256(f"{document_id}:{index}".encode("utf-8")).hexdigest()
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "file_title": file_title,
                    "item_name": item_name,
                    "content": chunk.page_content,
                    "section_path": chunk.metadata["section_path"],
                    "chunk_index": index,
                    "dense_vector": dense_vector,
                    "sparse_vector": sparse_vector,
                }
            )
        self._client.upsert(self._chunk_collection, data=rows)

        # 文档重新切分后若块数变少，删除上次导入留下的尾部块
        self._client.delete(
            collection_name=self._chunk_collection,
            filter=f'document_id == "{document_id}" and chunk_index >= {len(rows)}',
        )


def _connect_to_database() -> MilvusClient:
    """确保目标数据库存在，并创建连接到该数据库的客户端"""
    database_name = config.MILVUS_DATABASE
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,254}", database_name):
        raise ValueError(
            f"Milvus 数据库名无效：{database_name!r}；只能使用字母、数字和下划线，且不能以数字开头"
        )

    bootstrap_client = MilvusClient(uri=config.MILVUS_URI)
    try:
        if database_name not in bootstrap_client.list_databases():
            bootstrap_client.create_database(db_name=database_name)
            logger.info("创建 Milvus database: %s", database_name)
    finally:
        bootstrap_client.close()

    return MilvusClient(uri=config.MILVUS_URI, db_name=database_name)


@lru_cache(maxsize=1)
def get_embedding_store_client() -> EmbeddingStoreClient:
    return EmbeddingStoreClient()
