import logging
import re

from langchain_core.messages import HumanMessage
from langchain_core.messages.content import create_image_block

from core.exceptions import StateFieldError
from core.graphs.ingestion.state import IngestionState
from infrastructure.models.vision import vlm
from prompts.ingestion_prompts import IMAGE_SUMMARY_PROMPT

logger = logging.getLogger(__name__)

# 匹配图片
IMAGE_DATA_URI_RE = re.compile(
    r'!\[(?P<alt>[^]]*)]\(\s*'
    r'data:(?P<mime>image/[^;]+);base64,'
    r'(?P<data>.*?)\s*\)',
    re.DOTALL,
)

# 匹配标题
HEADING_RE = re.compile(r"(?m)^ {0,3}#{1,6}[ \t]+.+$")

MAX_CONTEXT_CHARS = 200


def summarize_images(state: IngestionState):
    """生成图片摘要并写入 Markdown 图片的 alt 文本"""
    _validate_state(state)
    markdown = state["markdown_content"]

    matches = list(IMAGE_DATA_URI_RE.finditer(markdown))
    logger.info("待生成摘要的图片: %d 张", len(matches))
    summarize_count = 0

    def replace_image(match: re.Match) -> str:
        nonlocal summarize_count
        context = _extract_image_context(markdown, match)

        mime_type = match.group("mime").lower()
        encoded = re.sub(r"\s+", "", match.group("data"))

        summary = _summarize_image(mime_type, encoded, context)
        alt_text = _escape_alt_text(summary)

        summarize_count += 1
        logger.info("图片摘要 (%d/%d) 张: %s", summarize_count, len(matches), alt_text[:50])

        return f"![{alt_text}](data:{mime_type};base64,{encoded})"

    updated_content = IMAGE_DATA_URI_RE.sub(replace_image, markdown)
    return {"markdown_content": updated_content}


def _validate_state(state: IngestionState) -> None:
    """校验状态"""
    if not state.get("markdown_content"):
        raise StateFieldError(
            node_name="summarize_images",
            field_name="markdown_content",
            message="Markdown内容不能为空",
        )


def _escape_alt_text(text: str) -> str:
    """清理摘要，避免破坏 Markdown 图片语法"""
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _extract_image_context(markdown: str, image_match: re.Match) -> dict[str, str]:
    """取图片所在章节的标题，以及图片前后的有限文本"""

    previous_heading = None
    for heading_match in HEADING_RE.finditer(markdown, 0, image_match.start()):
        previous_heading = heading_match

    next_heading = HEADING_RE.search(markdown, image_match.end())

    # 前文从最近一个标题之后开始；没有标题时从文档开头开始
    before_start = previous_heading.end() if previous_heading else 0

    # 后文到下一个标题之前结束；没有下一个标题时到文档结尾
    after_end = next_heading.start() if next_heading else len(markdown)

    before = markdown[before_start:image_match.start()]
    after = markdown[image_match.end():after_end]

    # 去掉相邻图片，避免占用上下文长度
    before = IMAGE_DATA_URI_RE.sub("[其他图片]", before).strip()
    after = IMAGE_DATA_URI_RE.sub("[其他图片]", after).strip()

    return {
        "heading": previous_heading.group(0).strip() if previous_heading else "",
        "before": _select_paragraph_context(before, from_end=True),
        "after": _select_paragraph_context(after, from_end=False),
    }


def _select_paragraph_context(text: str, *, from_end: bool) -> str:
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n[ \t]*\n+", text)
        if paragraph.strip()
    ]

    # 图片前从最近段落向前；图片后从最近段落向后
    candidates = list(reversed(paragraphs)) if from_end else paragraphs

    if not candidates:
        return ""

    # 最近段落本身超长，就只取靠近图片的一端
    nearest = candidates[0]
    if len(nearest) > MAX_CONTEXT_CHARS:
        return nearest[-MAX_CONTEXT_CHARS:] if from_end else nearest[:MAX_CONTEXT_CHARS]

    selected = [nearest]
    total_chars = len(nearest)

    # 最近段落未超限时，尽量加入更多完整段落
    for paragraph in candidates[1:]:
        added_chars = 2 + len(paragraph)  # 两个换行符作为段落分隔
        if total_chars + added_chars > MAX_CONTEXT_CHARS:
            break

        selected.append(paragraph)
        total_chars += added_chars

    if from_end:
        selected.reverse()

    return "\n\n".join(selected)


def _summarize_image(mime_type: str, encoded: str, context: dict[str, str]) -> str:
    prompt = IMAGE_SUMMARY_PROMPT.format(
        section_heading=context.get("heading") or "无",
        context_before_image=context.get("before") or "无",
        context_after_image=context.get("after") or "无",
    )

    response = vlm.invoke([
        HumanMessage(content=[
            {"type": "text", "text": prompt},
            create_image_block(
                base64=encoded,
                mime_type=mime_type,
            ),
        ])
    ])
    return response.text.strip()
