from pathlib import Path

from core.graphs.ingestion.nodes.chunk_document import chunk_document
from tests.helpers.chunk_io import save_chunks


def test_chunk_document_with_md():
    """测试从 Markdown 文件切分文档"""
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    pdf_path = fixtures_dir / "万用表RS-12的使用.pdf"
    md_path = fixtures_dir / "万用表RS-12的使用_upload_images.md"

    result = chunk_document({
        "file_path": str(pdf_path),
        "file_title": pdf_path.stem,
        "markdown_content": md_path.read_text(encoding="utf-8"),
    })

    assert result["chunks"]

    # 保存结果
    jsonl_path = fixtures_dir / "万用表RS-12的使用_chunks.jsonl"
    save_chunks(result["chunks"], jsonl_path)
