import logging
import time
from pathlib import Path
from typing import Dict

from mineru import parse

from core.exceptions import StateFieldError, ParseDocumentError
from core.graphs.ingestion.state import IngestionState


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
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            raise ParseDocumentError(
                node_name="parse_document",
                message=f"读取 Markdown 文件失败: {e}",
            ) from e
    else:
        try:
            logging.info(f"开始解析文件: {state['file_title']}")
            start_time = time.time()
            result = parse(path, tier="standard")
            logging.info(f"文件解析完成: {state['file_title']}, 耗时: {time.time() - start_time:.2f} 秒")

            content = result.markdown()
        except Exception as e:
            raise ParseDocumentError(
                node_name="parse_document",
                message=f"MinerU解析文档失败: {e}",
            ) from e

    return {"markdown_content": content}
