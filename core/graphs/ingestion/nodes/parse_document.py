import logging
from pathlib import Path
from typing import Dict

from mineru import parse

from core.exceptions import StateFieldError, ParseDocumentError
from core.graphs.ingestion.state import IngestionState

logger = logging.getLogger(__name__)


def parse_document(state: IngestionState) -> Dict:
    """解析文档"""
    path = Path(state["file_path"])

    if not path.is_file():
        raise StateFieldError(
            node_name="parse_document",
            field_name="file_path",
            message="文件不存在",
        )

    # Markdown 文件则直接读取，否则解析
    if path.suffix.lower() == ".md":
        logger.info("直接读取 Markdown: %s", path.name)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            raise ParseDocumentError(
                node_name="parse_document",
                message=f"读取 Markdown 文件失败: {e}",
            ) from e
    else:
        try:
            logger.info("解析文件: %s", path.name)
            result = parse(path, tier="standard")
            content = result.markdown()
        except Exception as e:
            raise ParseDocumentError(
                node_name="parse_document",
                message=f"MinerU解析文档失败: {e}",
            ) from e

    return {"markdown_content": content}
