from pathlib import Path

from core.graphs.ingestion.nodes.identify_item_name import identify_item_name
from tests.helpers.chunk_io import load_chunks


def test_identify_item_name():
    """测试识别产品名称"""
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    pdf_path = fixtures_dir / "万用表RS-12的使用.pdf"
    chunks_path = fixtures_dir / "万用表RS-12的使用_chunks.jsonl"

    result = identify_item_name({
        "file_path": str(pdf_path),
        "file_title": pdf_path.stem,
        "chunks": load_chunks(chunks_path),
    })

    assert result["item_name"].strip()
