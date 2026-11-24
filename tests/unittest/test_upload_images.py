from pathlib import Path

from core.graphs.ingestion.nodes.upload_images import upload_images


def test_upload_images_with_pdf():
    """测试上传图片到存储"""
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    pdf_path = fixtures_dir / "万用表RS-12的使用.pdf"
    md_path = fixtures_dir / "万用表RS-12的使用_summarize_images.md"

    result = upload_images({
        "file_path": str(pdf_path),
        "file_title": pdf_path.stem,
        "markdown_content": md_path.read_text(encoding="utf-8"),
    })

    assert result["markdown_content"].strip()
    assert "localhost:9000/store-guide" in result["markdown_content"]

    # 保存结果
    md_path = fixtures_dir / "万用表RS-12的使用_upload_images.md"
    md_path.write_text(result["markdown_content"], encoding="utf-8")
