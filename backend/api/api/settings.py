import json
import logging
from typing import Annotated, Any, Optional

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from pydantic import field_validator
from pydantic_settings import NoDecode

logger = logging.getLogger(__name__)


class Settings(CommonSettings):
    """All settings for the API service."""

    app_title: str = "Loom API"
    api_frontend_url: str = "api/"

    # Note: we can not use pydantic's HttpUrl here,
    # because it adds '/' at the end, which will
    # then break CORSMiddleware
    #
    # - https://github.com/pydantic/pydantic/issues/7186
    allowed_origins: Annotated[list[str], NoDecode] = [
        f"https://frontend.{DOMAIN}",
        f"http://frontend.{DOMAIN}",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    openapi_url: Optional[str] = "/openapi.json"
    swagger_ui_oauth2_redirect_url: str = "/docs/oauth2-redirect"


settings = Settings()

logger.debug(
    "Effective settings:\n%s",
    json.dumps(settings.model_dump(), indent=2, default=str),
)
