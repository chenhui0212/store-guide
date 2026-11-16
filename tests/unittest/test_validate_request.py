from pathlib import Path

import pytest

from core.exceptions import StateFieldError
from core.graphs.ingestion.nodes.validate_request import validate_request


def test_validate_request_with_pdf():
    """测试校验 PDF 文件"""
    file_name = "H3C LA2608室内无线网关 用户手册.pdf"
    pdf_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name

    result = validate_request({"file_path": str(pdf_path)})

    assert result["file_title"] == file_name.split(".")[0]


def test_validate_request_with_empty_file_path():
    """测试校验空文件路径"""
    with pytest.raises(StateFieldError, match="文件路径不能为空") as exc_info:
        validate_request({})

    assert exc_info.value.node_name == "validate_request"
    assert exc_info.value.field_name == "file_path"


def test_validate_request_with_invalid_file():
    """测试校验无效文件"""
    file_name = "invalid_file.pdf"
    invalid_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name

    with pytest.raises(StateFieldError, match="文件不存在") as exc_info:
        validate_request({"file_path": str(invalid_path)})

    assert exc_info.value.node_name == "validate_request"
    assert exc_info.value.field_name == "file_path"
