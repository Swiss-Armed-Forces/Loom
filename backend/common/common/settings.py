import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    AnyWebsocketUrl,
    Field,
    MongoDsn,
    field_validator,
)
from pydantic_settings import BaseSettings

from common.environment import get_loglevel, is_development_env
from common.services.encryption_service import AESMasterKey

logger = logging.getLogger(__name__)


DOMAIN: str = str(os.getenv("DOMAIN", "loom"))


class Settings(BaseSettings):
    """Settings for the common module They can be overridden by environment
    variables."""

    development_env: bool = Field(default_factory=is_development_env)
    loglevel: int = Field(default_factory=get_loglevel)
    # see: https://docs.python.org/3/library/codecs.html#error-handlers
    decode_error_handler: str = "backslashreplace"
    encode_error_handler: str = "backslashreplace"
    translate_target: str = "en"
    tempfile_dir: Path = Path.home() / ".loomcache"

    worker_type: Literal["WORKER", "REAPER", "FLOWER", "BEAT", "INSPECT"] = "INSPECT"
    worker_max_concurrency: int = 4

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
    max_file_size: int = 500_000_000  # 500 MB, because of rabbit
    translate_host: AnyHttpUrl = AnyHttpUrl(f"http://translate.{DOMAIN}")

    ollama_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}")
    ollama_tool_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama-tool.{DOMAIN}")
    ollama_timeout: int = 5 * 60

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:143")
    imap_user: str = "user"
    imap_password: str = "pass"

    llm_model: str = "smollm2:135m"
    llm_model_embedding: str = "nomic-embed-text:v1.5"
    llm_model_tool: str = "smollm2:135m"
    llm_think: bool = False
    llm_temperature: float | None = None

    task_time_limit__seconds: int = 3600

    llm_embedding_dimensions: int = (
        # Note: 4096 is largest vector supported by ElasticSearch
        768  # -> nomic-embed-text:v1.5
    )
    llm_system_prompt: str = """You are an expert english AI called Loom"""
    llm_summarize_system_prompt: str = (
        """You are an expert english summarization machine called Loom"""
    )

    roundcube_host: AnyHttpUrl = AnyHttpUrl(f"http://roundcube.{DOMAIN}")

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

    api_host: AnyHttpUrl = AnyHttpUrl(f"http://api.{DOMAIN}")
    ws_host: AnyWebsocketUrl = AnyWebsocketUrl(
        f"ws://api.{DOMAIN}",
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
