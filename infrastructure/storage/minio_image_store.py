from functools import lru_cache
from io import BytesIO
from urllib.parse import quote

from minio import Minio

import core.config as config


class ImageStoreClient:

    def __init__(self, client: Minio | None = None):
        self._client = client or Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_SECURE,
        )
        self._bucket = config.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def upload_image(self, image_bytes: bytes, content_type: str, object_name: str) -> str:
        """上传图片"""
        self._client.put_object(
            bucket_name=self._bucket,
            object_name=object_name,
            data=BytesIO(image_bytes),
            length=len(image_bytes),
            content_type=content_type,
        )

        scheme = "https" if config.MINIO_SECURE else "http"
        base_url = f"{scheme}://{config.MINIO_ENDPOINT}"
        return f"{base_url}/{self._bucket}/{quote(object_name, safe='/')}"


@lru_cache(maxsize=1)
def get_image_store_client() -> ImageStoreClient:
    return ImageStoreClient()
