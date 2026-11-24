from pathlib import Path

from core.graphs.ingestion.nodes.embed_document import embed_document
from tests.helpers.chunk_io import load_chunks


def test_embed_document():
    """测试向量化文档"""
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

    assert result["item_name_dense_embedding"]
    assert result["item_name_sparse_embedding"]
    assert len(result["chunk_dense_embeddings"]) == len(chunks)
    assert len(result["chunk_sparse_embeddings"]) == len(chunks)
