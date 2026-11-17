from pathlib import Path

from core.graphs.ingestion.nodes.summarize_images import summarize_images, IMAGE_DATA_URI_RE


def test_summarize_images_with_pdf():
    """测试从 PDF 文件中的图片生成摘要"""
    file_name = "H3C LA2608室内无线网关 用户手册.pdf"
    md_file_name = "H3C LA2608室内无线网关 用户手册.md"
    pdf_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name
    md_path = Path(__file__).resolve().parents[1] / "fixtures" / md_file_name

    result = summarize_images({
        "file_path": str(pdf_path),
        "file_title": Path(file_name).stem,
        "markdown_content": Path(md_path).read_text(encoding="utf-8"),
    })

    assert result["markdown_content"].strip()

    images = list(IMAGE_DATA_URI_RE.finditer(result["markdown_content"]))
    assert images, "没有找到图片"
    assert all(image.group("alt").strip() for image in images), "存在没有简介的图片"
