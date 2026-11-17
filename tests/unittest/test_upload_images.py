from pathlib import Path

from core.graphs.ingestion.nodes.upload_images import upload_images


def test_upload_images_with_pdf():
    """测试上传图片到存储"""
    file_name = "H3C LA2608室内无线网关 用户手册.pdf"
    md_file_name = "H3C LA2608室内无线网关 用户手册.md"
    pdf_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name
    md_path = Path(__file__).resolve().parents[1] / "fixtures" / md_file_name

    result = upload_images({
        "file_path": str(pdf_path),
        "file_title": Path(file_name).stem,
        "markdown_content": Path(md_path).read_text(encoding="utf-8"),
    })

    assert result["markdown_content"].strip()
    assert "localhost:9000/store-guide" in result["markdown_content"]
