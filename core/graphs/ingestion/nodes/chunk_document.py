import logging
import re
from typing import Any

from chonkie import TableChef, TableChunker
from langchain_core.documents import Document
from langchain_text_splitters import (
    ExperimentalMarkdownSyntaxTextSplitter,
    RecursiveCharacterTextSplitter,
)

import core.config as config
from core.exceptions import StateFieldError
from core.graphs.ingestion.state import IngestionState

logger = logging.getLogger(__name__)

HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]

_HTML_TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table\s*>", re.IGNORECASE | re.DOTALL)
_HTML_ROW_RE = re.compile(r"<tr\b[^>]*>.*?</tr\s*>", re.IGNORECASE | re.DOTALL)
_HTML_TBODY_OPEN_RE = re.compile(r"<tbody\b[^>]*>", re.IGNORECASE)
_HTML_THEAD_OPEN_RE = re.compile(r"<thead\b[^>]*>", re.IGNORECASE)
_HTML_TABLE_CLOSE_RE = re.compile(r"</table\s*>", re.IGNORECASE)


def chunk_document(state: IngestionState) -> dict[str, Any]:
    """切分 Markdown 文档"""
    _validate_state(state)

    # 按标题切分
    sections: list[Document] = ExperimentalMarkdownSyntaxTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=True,
    ).split_text(state["markdown_content"])

    # 合并过短的小节
    merged_sections = _merge_small_sections(sections)

    # 过长再切分
    chunks = _split_oversized_sections(merged_sections, state)
    return {"chunks": chunks}


def _validate_state(state: IngestionState) -> None:
    markdown = state.get("markdown_content")
    if not isinstance(markdown, str) or not markdown.strip():
        raise StateFieldError(
            field_name="markdown_content",
            node_name="chunk_document",
            message="Markdown 内容不能为空",
        )


def _merge_small_sections(sections: list[Document]) -> list[Document]:
    """按 H4/H3/H2 层级合并短小节"""
    merge_trigger = config.CHUNK_SIZE // 4
    merge_cap = config.CHUNK_SIZE * 3 // 4

    def render_section(section: Document, from_level: int) -> str:
        headings = [
            f"{'#' * heading_level} {section.metadata[f'h{heading_level}']}"
            for heading_level in range(from_level, 5)
            if section.metadata.get(f"h{heading_level}")
        ]
        parts = [*headings, section.page_content.strip()]
        return "\n\n".join(part for part in parts if part).strip()

    def parent_prefix(section: Document, level: int) -> str:
        path = " > ".join(
            section.metadata[f"h{parent_level}"]
            for parent_level in range(1, level)
            if section.metadata.get(f"h{parent_level}")
        )
        return f"{path}\n\n" if path else ""

    for level in (4, 3, 2):
        merged: list[Document] = []
        current: Document | None = None
        current_was_merged = False

        def flush_current() -> None:
            nonlocal current, current_was_merged
            if current is None:
                return

            if current_was_merged:
                # 合并过的子标题已写入正文，metadata 保留共同父标题
                for child_level in range(level, 5):
                    current.metadata.pop(f"h{child_level}", None)
                current.metadata["section_path"] = " > ".join(
                    current.metadata[key].strip()
                    for key in ("h1", "h2", "h3", "h4")
                    if isinstance(current.metadata.get(key), str)
                    and current.metadata[key].strip()
                )

            merged.append(current)
            current = None
            current_was_merged = False

        for section in sections:
            if current is None:
                current = section
                continue

            parent_keys = [f"h{parent_level}" for parent_level in range(1, level)]
            same_parent = all(
                current.metadata.get(key) == section.metadata.get(key)
                for key in parent_keys
            )

            current_text = (
                current.page_content.strip()
                if current_was_merged
                else render_section(current, level)
            )
            next_text = render_section(section, level)
            prefix = parent_prefix(current, level)
            current_size = len(prefix) + len(current_text)
            next_size = len(prefix) + len(next_text)
            merge_started = (
                    current_was_merged
                    or min(current_size, next_size) < merge_trigger
            )
            combined_size = len(prefix) + len(current_text) + 2 + len(next_text)

            if same_parent and merge_started and combined_size <= merge_cap:
                if not current_was_merged:
                    current.page_content = current_text
                current.page_content = (
                    f"{current.page_content.rstrip()}\n\n{next_text}"
                )
                current_was_merged = True
                continue

            flush_current()
            current = section

        flush_current()
        sections = merged

    return sections


def _split_oversized_sections(sections: list[Document], state: IngestionState) -> list[Document]:
    """拆分超过长度的小节"""
    chunks: list[Document] = []
    for section in sections:
        # 标题路径
        section_path = " > ".join(
            section.metadata[key].strip()
            for key in ("h1", "h2", "h3", "h4")
            if isinstance(section.metadata.get(key), str) and section.metadata[key].strip()
        )
        prefix = f"{section_path}" if section_path else ""
        body_size = config.CHUNK_SIZE - len(prefix)

        section_content = section.page_content.strip()
        if len(section_content) > body_size:
            section_chunks = _split_section_content(section_content, body_size)
        else:
            section_chunks = [section_content]

        # 构建文档块
        for section_chunk in section_chunks:
            content = section_chunk.strip()
            if not content:
                continue

            if prefix:
                content = f"{prefix}\n\n{content}"

            metadata: dict[str, Any] = {
                "file_title": state.get("file_title", ""),
                "section_path": section_path,
                "chunk_index": len(chunks),
            }
            chunks.append(Document(page_content=content, metadata=metadata))

    logger.info("文档切分完成: file=%s chunks=%d", state.get("file_title", ""), len(chunks))
    if logger.isEnabledFor(logging.DEBUG):
        for chunk in chunks:
            logger.debug(f"chunk {chunk.metadata['chunk_index']}:{chunk.metadata}\n{chunk.page_content}\n\n")
    return chunks


def _split_section_content(content: str, chunk_size: int) -> list[str]:
    """切分小节内容"""
    markdown_document = TableChef().parse(content)
    tables = sorted(markdown_document.tables, key=lambda table: table.start_index)

    prose_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    table_splitter = TableChunker(tokenizer="character", chunk_size=chunk_size)

    chunks: list[str] = []
    cursor = 0

    def append_prose(prose: str) -> None:
        if prose.strip():
            chunks.extend(prose_splitter.split_text(prose.strip()))

    for table in tables:
        if table.start_index < cursor:
            continue

        append_prose(content[cursor:table.start_index])
        table_content = _prepare_html_table_header(table.content)
        table_chunks = table_splitter.chunk(table_content)

        # 对格式不完整、无法切分的表格做保底，避免静默丢掉原文
        chunks.extend(chunk.text for chunk in table_chunks if chunk.text.strip())
        if not table_chunks and table_content.strip():
            chunks.append(table_content.strip())

        cursor = table.end_index

    append_prose(content[cursor:])
    return chunks


def _prepare_html_table_header(table: str) -> str:
    """为未包含 thead/tbody 的简单 HTML 表格标记首行为表头"""
    if not _HTML_TABLE_RE.fullmatch(table.strip()):
        return table

    if _HTML_THEAD_OPEN_RE.search(table) or _HTML_TBODY_OPEN_RE.search(table):
        return table

    first_row = _HTML_ROW_RE.search(table)
    table_close = _HTML_TABLE_CLOSE_RE.search(table)
    if not first_row or not table_close or first_row.end() > table_close.start():
        return table

    # 将首行的 td 标记为 th，保留单元格属性和内容
    header_row = re.sub(
        r"(<\s*/?\s*)td(\b[^>]*>)",
        r"\1th\2",
        first_row.group(0),
        flags=re.IGNORECASE,
    )

    # 首行作为表头，剩余行作为数据行
    return (
            table[:first_row.start()]
            + f"<thead>{header_row}</thead><tbody>"
            + table[first_row.end():table_close.start()]
            + "</tbody>"
            + table[table_close.start():]
    )
