import hashlib
import mimetypes

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/svg+xml": ".svg",
}


def get_image_extension(mime_type) -> str:
    extension = (
            IMAGE_EXTENSIONS.get(mime_type)
            or mimetypes.guess_extension(mime_type)
    )
    if extension is None:
        raise ValueError(f"不支持的图片类型：{mime_type}")
    return extension


def generate_file_name(mime_type: str, image_bytes: bytes) -> str:
    """生成图片文件名"""
    digest = hashlib.sha256(image_bytes).hexdigest()
    extension = get_image_extension(mime_type)
    return f"{digest}{extension}"
