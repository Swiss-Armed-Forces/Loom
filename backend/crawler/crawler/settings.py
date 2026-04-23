"""Settings for the crawler."""

from common.settings import S3StorageSettings
from common.settings import Settings as CommonSettings


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"

    s3_storage: S3StorageSettings = S3StorageSettings(
        bucket_name="default",
    )
    s3_bucket_alias: str | None = None


settings = Settings()
