"""Settings for the crawler."""

import os
from pathlib import Path
from typing import Annotated

from common.settings import Settings as CommonSettings
from pydantic import DirectoryPath, Field

MINIO_ACCESS_KEY: str = "MinIO-Intake-Key"
MINIO_SECRET_KEY: str = str(os.getenv("MINIO_SECRET_KEY", "minioadmin"))


class Settings(CommonSettings):
    """All settings for the crawler."""

    intake_dir: Annotated[Path, DirectoryPath] = Field(
        default=Path("/intake"), description="Directory to watch for new files"
    )
    crawler_source_id: str = "crawler"
    minio_default_bucket_name: str = "default"


settings = Settings()
