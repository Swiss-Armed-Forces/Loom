"""Settings for the crawler."""

import os

from common.settings import Settings as CommonSettings

MINIO_ACCESS_KEY: str = "MinIO-Intake-Key"
MINIO_SECRET_KEY: str = str(os.getenv("MINIO_SECRET_KEY", "minioadmin"))


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"
    minio_default_bucket_name: str = "default"


settings = Settings()
