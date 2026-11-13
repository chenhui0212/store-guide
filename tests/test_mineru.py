from pathlib import Path

from mineru.parser import parse

tests_dir = Path(__file__).resolve().parent

def test_parse():
    """测试解析 PDF 文件"""
    pdf_dir = tests_dir / "mineru"
    result = parse(
        pdf_dir / "万用表RS-12的使用.pdf",
        tier="standard",
        ocr_mode="auto",
        page_range="all",
    )
    Path(pdf_dir / "万用表RS-12的使用.md").write_text(result.markdown(), encoding="utf-8")
