from pathlib import Path
from typing import Dict

import core.config as config
from core.exceptions import StateFieldError
from ..state import IngestionState


def validate_request(state: IngestionState) -> Dict:
    """校验请求"""
    file_path = state.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise StateFieldError(
            node_name="validate_request",
            field_name="file_path",
            message="文件路径不能为空",
        )

    path = Path(file_path)
    if not path.is_file():
        raise StateFieldError(
            node_name="validate_request",
            field_name="file_path",
            message="文件不存在",
        )

    if path.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
        raise StateFieldError(
            node_name="validate_request",
            field_name="file_path",
            message="暂不支持该文件格式",
        )

    if path.stat().st_size > config.MAX_FILE_SIZE:
        raise StateFieldError(
            node_name="validate_request",
            field_name="file_path",
            message="文件超过大小限制",
        )

    return {"file_title": path.stem}
