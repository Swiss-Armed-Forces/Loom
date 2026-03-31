import logging
import os
from pathlib import Path
from socket import gethostname
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    AnyWebsocketUrl,
    BaseModel,
    Field,
    MongoDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.environment import get_loglevel, is_development_env
from common.services.encryption_service import AESMasterKey

logger = logging.getLogger(__name__)


def _get_persister_id_from_hostname() -> int:
    """Extract persister ID from StatefulSet pod hostname.

    StatefulSet pods have hostnames like 'loom-persister-0', 'loom-persister-1', etc.
    Extract the ordinal suffix as the persister ID.
    """
    hostname = os.environ.get("HOSTNAME", gethostname())
    try:
        return int(hostname.rsplit("-", 1)[-1])
    except (ValueError, IndexError):
        return 0  # Default for non-StatefulSet environments


DOMAIN: str = str(os.getenv("DOMAIN", "loom"))


class S3StorageSettings(BaseModel):
    bucket_name: str
    s3_host: str = f"s3.{DOMAIN}"
    s3_secret_key: str | None = None
    s3_access_key: str | None = None
    s3_secure_connection: bool = False


class Settings(BaseSettings):
    """Settings for the common module They can be overridden by environment
    variables."""

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    development_env: bool = Field(default_factory=is_development_env)
    loglevel: int = Field(default_factory=get_loglevel)
    # see: https://docs.python.org/3/library/codecs.html#error-handlers
    decode_error_handler: str = "backslashreplace"
    encode_error_handler: str = "backslashreplace"
    translate_target: str = "en"
    tempfile_dir: Path = Path.home() / ".loomcache"

    worker_type: Literal[
        "WORKER",
        "REAPER",
        "FLOWER",
        "BEAT",
        "PERSISTER",
        "INSPECT",
    ] = "INSPECT"
    worker_max_concurrency: int = 4
    num_persister_shards: int = 16
    persister_total: int = 1  # Total number of PERSISTER workers
    persister_id: int = Field(default_factory=_get_persister_id_from_hostname)

    # Threshold for considering queues "idle" in periodic tasks.
    # Set > 0 because the periodic task itself is counted in the queue.
    periodic_consider_queue_idle_threshold: int = 5

    mongo_db_host: MongoDsn = MongoDsn(f"mongodb://mongodb.{DOMAIN}")
    mongo_db_file_storage_name: str = "files"
    mongo_db_system_file_storage_name: str = "systemfiles"
    mongo_db_lazybytes_storage_name: str = "lazybytes"
    mongo_db_repositories_storage_name: str = "repositories"

    es_host: AnyHttpUrl = AnyHttpUrl(f"http://elasticsearch.{DOMAIN}")
    es_timeout: int = 120
    es_number_of_shards: int = 1
    es_number_of_replicas: int = 0
    rabbit_mq_management_host: AnyHttpUrl = AnyHttpUrl(
        f"http://guest:guest@rabbit.{DOMAIN}"
    )
    celery_broker_host: AnyUrl = AnyUrl(f"amqp://rabbit-amqp.{DOMAIN}")
    celery_backend_host: AnyUrl = AnyUrl(f"redis://redis.{DOMAIN}:6379/0?protocol=3")
    redis_cache_host: AnyUrl = AnyUrl(f"redis://redis-cache.{DOMAIN}:6380/0?protocol=3")
    lazy_threshold_bytes: int = 1024  # 1KiB
    translate_host: AnyHttpUrl = AnyHttpUrl(f"http://translate.{DOMAIN}")
    translate_timeout: int = 3 * 60
    translate_startup_timeout: int = (
        10  # used only for fetching languages during app startup
    )

    ollama_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}")
    ollama_tool_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama-tool.{DOMAIN}")
    ollama_timeout: int = 5 * 60

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:143")
    imap_user: str = "user"
    imap_password: str = "pass"

    llm_model: str = "smollm2:135m"
    llm_model_embedding: str = "nomic-embed-text-v2-moe"
    llm_model_tool: str = "smollm2:135m"
    llm_think: bool = False
    llm_temperature: float | None = None

    task_time_limit__seconds: int = 60 * 60 * 24

    llm_embedding_dimensions: int = (
        # Note: 4096 is largest vector supported by ElasticSearch
        768  # -> nomic-embed-text-v2-moe
    )
    llm_system_prompt: str = """You are an expert english AI called Loom"""
    llm_summarize_system_prompt: str = (
        """You are an expert english summarization machine called Loom"""
    )

    roundcube_host: AnyHttpUrl = AnyHttpUrl(f"http://roundcube.{DOMAIN}")

    # SeaweedFS Configuration
    seaweedfs_master_host: AnyHttpUrl = AnyHttpUrl(
        f"http://seaweedfs-master.{DOMAIN}:9333"
    )

    random_source: bytes | None = None

    archive_enc_master_key: AESMasterKey | None = None

    automatic_indexing: bool = True

    @field_validator("archive_enc_master_key", mode="before")
    @classmethod
    def parse_archive_enc_master_key(cls, value: str) -> AESMasterKey:
        if isinstance(value, str):
            return AESMasterKey.from_string(value)
        logger.warning("No archive encryption master key provided. Using fixed key.")
        return AESMasterKey.from_fixed_key()

    @model_validator(mode="after")
    def adjust_lazy_threshold_for_reaper(self) -> "Settings":
        if self.worker_type == "REAPER":
            self.lazy_threshold_bytes = 0
        return self

    @model_validator(mode="after")
    def validate_persister_total(self) -> "Settings":
        if self.persister_total > self.num_persister_shards:
            raise ValueError(
                f"persister_total ({self.persister_total}) cannot exceed "
                f"num_persister_shards ({self.num_persister_shards})"
            )
        return self

    @model_validator(mode="after")
    def validate_persister_id(self) -> "Settings":
        if self.persister_id >= self.persister_total:
            raise ValueError(
                f"persister_id ({self.persister_id}) must be less than "
                f"persister_total ({self.persister_total})"
            )
        return self

    api_host: AnyHttpUrl = AnyHttpUrl(f"http://api.{DOMAIN}")
    ws_host: AnyWebsocketUrl = AnyWebsocketUrl(
        f"ws://api.{DOMAIN}",
    )

    file_storage: S3StorageSettings = S3StorageSettings(bucket_name="loom-filestorage")
    lazybytes_storage: S3StorageSettings = S3StorageSettings(
        bucket_name="loom-lazybytes"
    )


settings = Settings()

if settings.development_env:
    logger.warning(
        "\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!! DO NOT USE THIS IN PRODUCTION !!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    )
