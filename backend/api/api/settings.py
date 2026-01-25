from typing import Optional

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings


class Settings(CommonSettings):
    """All settings for the API service."""

    app_title: str = "Loom API"
    api_frontend_url: str = "api/"

    # Note: we can not use pydantic's HttpUrl here,
    # because it adds '/' at the end, which will
    # then break CORSMiddleware
    #
    # - https://github.com/pydantic/pydantic/issues/7186
    allowed_origins: list[str] = [
        f"https://frontend.{DOMAIN}",
        f"http://frontend.{DOMAIN}",
    ]
    openapi_url: Optional[str] = "/openapi.json"
    swagger_ui_oauth2_redirect_url: str = "/docs/oauth2-redirect"


settings = Settings()
