import logging

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

import core.config as config
from core.exceptions import LLMError, StateFieldError
from core.graphs.ingestion.state import IngestionState
from infrastructure.models.chat import chat_llm
from prompts.ingestion_prompts import ITEM_NAME_SYSTEM_PROMPT, ITEM_NAME_USER_PROMPT

logger = logging.getLogger(__name__)


class ItemNameExtraction(BaseModel):
    """产品名称抽取结果"""
    item_name: str = Field(description="产品的完整名称")


item_name_extractor = chat_llm.with_structured_output(
    ItemNameExtraction,
    method="function_calling",
)


def identify_item_name(state: IngestionState) -> dict[str, str]:
    """识别产品名称"""
    _validate_state(state)

    file_title = state["file_title"]
    try:
        messages = [
            SystemMessage(ITEM_NAME_SYSTEM_PROMPT),
            HumanMessage(
                ITEM_NAME_USER_PROMPT.format(
                    file_title=file_title,
                    manual_excerpt=_build_manual_excerpt(state["chunks"]),
                )
            ),
        ]
        result: ItemNameExtraction = item_name_extractor.invoke(messages)
    except Exception as e:
        raise LLMError(
            f"产品名称识别失败: {e}",
            node_name="identify_item_name",
        ) from e

    item_name = " ".join(result.item_name.split())
    if item_name:
        logger.info("产品名称识别完成: file=%s item_name=%s", file_title, item_name)
    else:
        item_name = file_title
        logger.info("产品名称识别失败，使用文件标题替代: file=%s item_name=%s", file_title, item_name)

    for chunk in state["chunks"]:
        chunk.metadata["item_name"] = item_name
    return {"item_name": item_name}


def _validate_state(state: IngestionState) -> None:
    """校验状态"""
    if not state.get("file_title"):
        raise StateFieldError(
            node_name="identify_item_name",
            field_name="file_title",
            message="文件标题不能为空",
        )

    chunks = state.get("chunks")
    if not chunks or not isinstance(chunks, list):
        raise StateFieldError(
            node_name="identify_item_name",
            field_name="chunks",
            message="文档块不能为空",
            expected_type=list
        )


def _build_manual_excerpt(chunks: list[Document]) -> str:
    """构建手册摘要"""
    excerpt_parts = []
    excerpt_chars = 0
    max_chars = config.ITEM_NAME_MAX_CONTEXT_CHARS

    for chunk in chunks[:config.ITEM_NAME_MAX_CHUNKS]:
        text = chunk.page_content
        if not text:
            continue

        if excerpt_chars + len(text) > max_chars:
            continue

        excerpt_parts.append(text)
        excerpt_chars += len(text)

    return "\n\n".join(excerpt_parts)
