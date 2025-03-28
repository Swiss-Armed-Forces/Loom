"""Settings for the crawler."""

import os

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from pydantic import Field

MINIO_ACCESS_KEY: str = "MinIO-Intake-Key"
MINIO_SECRET_KEY: str = str(os.getenv("MINIO_SECRET_KEY", "minioadmin"))


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"
    minio_default_bucket_name: str = "default"

    minio_host: str = f"minio-api.{DOMAIN}"
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY", default="minioadmin")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY", default="minioadmin")
    minio_secure_connection: bool = False


settings = Settings()
