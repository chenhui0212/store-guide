import base64
import logging
import re

from core.exceptions import StateFieldError, StorageError
from core.graphs.ingestion.state import IngestionState
from infrastructure.storage.minio_image_storage import ImageStorageClient
from utils import image_utils

logger = logging.getLogger(__name__)

IMAGE_DATA_URI_RE = re.compile(
    r'!\[(?P<alt>[^]]*)]\(\s*'
    r'data:(?P<mime>image/[^;]+);base64,'
    r'(?P<data>.*?)\s*\)',
    re.DOTALL,
)


def upload_images(state: IngestionState):
    """上传图片到存储"""
    _validate_state(state)

    client = ImageStorageClient()

    matches = list(IMAGE_DATA_URI_RE.finditer(state["markdown_content"]))
    logger.info("待上传的图片: %d 张", len(matches))
    uploaded_count = 0

    def replace_image(match: re.Match) -> str:
        nonlocal uploaded_count
        mime_type = match.group("mime").lower()

        try:
            image_bytes = base64.b64decode(
                re.sub(r"\s+", "", match.group("data")),
                validate=True,
            )
        except Exception as e:
            raise StorageError(
                node_name="upload_images",
                message=f"解码图片失败：{e}",
            ) from e

        # 生成图片文件名
        try:
            image_file_name = image_utils.generate_file_name(mime_type, image_bytes)
        except ValueError as e:
            raise StorageError(
                node_name="upload_images",
                message=f"生成图片文件名失败：{e}",
            ) from e

        # 上传图片
        try:
            uploaded_url = client.upload_image(
                image_bytes=image_bytes,
                content_type=mime_type,
                object_name=f"{state['file_title']}/{image_file_name}",
            )
        except Exception as e:
            raise StorageError(
                node_name="upload_images",
                message=f"上传图片失败：{e}",
            ) from e

        uploaded_count += 1
        logger.info("图片上传完成: %s (%d/%d)", image_file_name, uploaded_count, len(matches))

        return f"![{match.group('alt')}]({uploaded_url})"

    updated_content = IMAGE_DATA_URI_RE.sub(
        replace_image,
        state["markdown_content"]
    )
    return {"markdown_content": updated_content}


def _validate_state(state: IngestionState) -> None:
    """校验状态"""
    if not state.get("markdown_content"):
        raise StateFieldError(
            node_name="upload_images",
            field_name="markdown_content",
            message="Markdown内容不能为空",
        )

    if not state.get("file_title"):
        raise StateFieldError(
            node_name="upload_images",
            field_name="file_title",
            message="文件标题不能为空",
        )
