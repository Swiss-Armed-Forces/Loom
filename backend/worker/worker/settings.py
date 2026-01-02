from datetime import timedelta
from typing import Any, Tuple, Type

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from pydantic import AnyHttpUrl, AnyUrl
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)

from worker.services.tika_languages import TikaAllowedOcrLanguage


class SettingsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "tika_ocr_languages":
            if value:
                return list(value.split(","))
        return value


class Settings(CommonSettings):
    """All settings for the worker service."""

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

    skip_translate_while_indexing: bool = True
    skip_summarize_while_indexing: bool = True
    min_language_detection_confidence: float = 95.0
    persist_success_tasks: bool = False
    persist_retry_tasks: bool = True
    tika_ocr_languages: list[TikaAllowedOcrLanguage] = ["eng"]
    tika_server_host: AnyHttpUrl = AnyHttpUrl(f"http://tika.{DOMAIN}")

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:143")
    imap_user: str = "user"
    imap_password: str = "pass"

    rspam_host: AnyHttpUrl = AnyHttpUrl(f"http://rspamd-worker.{DOMAIN}")

    llm_summarize_text_chunk_size: int = 3000
    llm_summarize_text_chunk_overlap: int = 100
    summary_max_chunks: int = 5
    uploaded_files_time_before_hidden: timedelta = timedelta(days=90)

    llm_embedding_temperature: float | None = 0

    llm_embedding_text_chunk_size: int = 500
    llm_embedding_text_chunk_overlap: int = 50

    llm_rerank_temperature: float | None = None
    llm_rerank_system_prompt: str = (
        """You are an expert reranking machine called Loom"""
    )

    llm_chat_system_prompt: str = """You are an expert english chatbot called Loom"""
    llm_chat_message_history_index: str = "message_history"


settings = Settings()
