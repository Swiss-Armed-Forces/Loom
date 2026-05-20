"""Settings for the crawler."""

from common.settings import Settings as CommonSettings


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"
    s3_bucket_alias: str | None = None


settings = Settings()
