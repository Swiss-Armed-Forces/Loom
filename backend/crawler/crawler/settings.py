"""Settings for the crawler."""

from typing import Any

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from pydantic.fields import FieldInfo
from pydantic_settings import (
    EnvSettingsSource,
)


class CrawlerEnvSettingsSource(EnvSettingsSource):
    """Custom settings source that parses comma-separated values for s3_buckets."""

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "s3_buckets":
            if value:
                return list(value.split(","))
        return value


class Settings(CommonSettings):
    """All settings for the crawler."""

    crawler_source_id: str = "crawler"

    s3_host: str = f"s3.{DOMAIN}"
    s3_secure_connection: bool = False

    s3_bucket_names: list[str] = ["default"]


settings = Settings()
