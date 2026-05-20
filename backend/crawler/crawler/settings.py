"""Settings for the crawler."""

import json
import logging

from common.settings import Settings as CommonSettings

logger = logging.getLogger(__name__)


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"
    s3_bucket_alias: str | None = None


settings = Settings()

logger.debug(
    "Effective settings:\n%s",
    json.dumps(settings.model_dump(), indent=2, default=str),
)
