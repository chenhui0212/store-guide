from pathlib import Path
from core.graphs.ingestion.nodes.parse_document import parse_document


def test_parse_document_with_pdf():
    """测试解析 PDF 文件"""
    file_name = "H3C LA2608室内无线网关 用户手册.pdf"
    pdf_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name

    result = parse_document({"file_path": str(pdf_path)})

    assert result["markdown_content"].strip()
    assert "H3C LA2608 室内无线网关" in result["markdown_content"]