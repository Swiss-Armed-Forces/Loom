from common.settings import Settings as CommonSettings
from pydantic import Field


class Settings(CommonSettings):
    # hostname of current container
    current_container_hostname: str = Field(alias="HOSTNAME", default="")


settings = Settings()
