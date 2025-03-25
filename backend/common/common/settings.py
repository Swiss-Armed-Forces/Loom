import logging
import os
from pathlib import Path
from typing import Any, Tuple, Type

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    AnyWebsocketUrl,
    Field,
    MongoDsn,
    field_validator,
)
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)

from common.environment import get_loglevel, is_development_env, is_test_env
from common.services.encryption_service import AESMasterKey
from common.tika_languages import TikaAllowedOcrLanguage

logger = logging.getLogger(__name__)


DOMAIN: str = str(os.getenv("DOMAIN", "loom"))


class SettingsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "tika_ocr_languages":
            if value:
                return list(value.split(","))
        return value


class Settings(BaseSettings):
    """Settings for the common module They can be overridden by environment
    variables."""

    # pylint: disable=too-many-arguments
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (SettingsSource(settings_cls),)

    development_env: bool = Field(default_factory=is_development_env)
    test_env: bool = Field(default_factory=is_test_env)
    loglevel: int = Field(default_factory=get_loglevel)
    # see: https://docs.python.org/3/library/codecs.html#error-handlers
    decode_error_handler: str = "backslashreplace"
    encode_error_handler: str = "backslashreplace"
    translate_target: str = "en"
    tempfile_dir: Path = Path.home() / ".loomcache"

    mongo_db_host: MongoDsn = MongoDsn(f"mongodb://mongodb.{DOMAIN}")
    mongo_db_file_storage_name: str = "files"
    mongo_db_system_file_storage_name: str = "systemfiles"
    mongo_db_lazybytes_storage_name: str = "lazybytes"
    mongo_db_repositories_storage_name: str = "repositories"

    es_host: AnyHttpUrl = AnyHttpUrl(f"http://elasticsearch.{DOMAIN}")
    es_timeout: int = 120
    rabbit_mq_management_host: AnyHttpUrl = AnyHttpUrl(
        f"http://guest:guest@rabbit.{DOMAIN}"
    )
    celery_broker_host: AnyUrl = AnyUrl(f"amqp://rabbit-amqp.{DOMAIN}")
    celery_backend_host: AnyUrl = AnyUrl(f"redis://redis.{DOMAIN}/0?protocol=3")
    tika_server_host: AnyHttpUrl = AnyHttpUrl(f"http://tika.{DOMAIN}")
    max_file_size: int = 500_000_000  # 500 MB, because of rabbit
    rspam_host: AnyHttpUrl = AnyHttpUrl(f"http://rspamd-worker.{DOMAIN}")
    libretranslate_host: AnyHttpUrl = AnyHttpUrl(f"http://libretranslate.{DOMAIN}")
    ollama_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}")
    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}")
    imap_user: str = "user"
    imap_password: str = "pass"
    imap_directory: str = "INBOX"

    llm_model: str = "deepseek-r1:8b"
    llm_model_embedding: str = "nomic-embed-text:v1.5"
    llm_temperature: float | None = None
    llm_timeout: int = 5 * 60
    llm_summarize_system_prompt: str = (
        """You are an expert english summarization machine called Loom"""
    )

    llm_summarize_text_chunk_size: int = 3000
    llm_summarize_text_chunk_overlap: int = 100

    llm_embedding_dimensions: int = (
        # Note: 4096 is largest vector supported by ElasticSearch
        768  # -> nomic-embed-text:v1.5
    )
    llm_embedding_temperature: float | None = 0

    llm_embedding_text_chunk_size: int = 500
    llm_embedding_text_chunk_overlap: int = 50

    llm_rerank_temperature: float | None = None
    llm_rerank_system_prompt: str = (
        """You are an expert reranking machine called Loom"""
    )

    llm_chat_system_prompt: str = """You are an expert english chatbot called Loom"""
    llm_chat_message_history_index: str = "message_history"

    random_source: bytes | None = None

    archive_encryption_master_key: AESMasterKey | None = None

    @field_validator("archive_encryption_master_key", mode="before")
    @classmethod
    def parse_archive_encryption_master_key(cls, value: str) -> AESMasterKey:
        if isinstance(value, str):
            return AESMasterKey.from_string(value)
        logger.warning("No archive encryption master key provided. Using fixed key.")
        return AESMasterKey.from_fixed_key()

    tika_ocr_languages: list[TikaAllowedOcrLanguage] = ["eng"]

    api_host: AnyHttpUrl = AnyHttpUrl(f"http://api.{DOMAIN}")
    ws_host: AnyWebsocketUrl = AnyWebsocketUrl(
        f"ws://api.{DOMAIN}",
    )

    minio_host: str = f"minio-api.{DOMAIN}"
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY", default="minioadmin")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY", default="minioadmin")
    minio_secure_connection: bool = False


settings = Settings()

if settings.development_env or settings.test_env:
    logger.warning(
        "\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!! DO NOT USE THIS IN PRODUCTION !!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    )
