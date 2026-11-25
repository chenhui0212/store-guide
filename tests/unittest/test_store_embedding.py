from pathlib import Path

from core.graphs.ingestion.nodes.embed_document import embed_document
from core.graphs.ingestion.nodes.store_embeddings import store_embeddings
from tests.helpers.chunk_io import load_chunks


def test_store_embeddings():
    """测试存储向量"""
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    pdf_path = fixtures_dir / "万用表RS-12的使用.pdf"
    chunks_path = fixtures_dir / "万用表RS-12的使用_chunks.jsonl"
    item_name = "RS-12 数字万用表"

    chunks = load_chunks(chunks_path)
    for chunk in chunks:
        chunk.metadata["item_name"] = item_name

    result = embed_document({
        "file_path": str(pdf_path),
        "file_title": pdf_path.stem,
        "item_name": item_name,
        "chunks": chunks,
    })

    store_embeddings({
        "file_path": str(pdf_path),
        "file_title": pdf_path.stem,
        "item_name": item_name,
        "chunks": chunks,
        **result,
    })
