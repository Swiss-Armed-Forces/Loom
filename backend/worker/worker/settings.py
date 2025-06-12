from typing import Any, Tuple, Type

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from pydantic import AnyHttpUrl
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

    skip_translate_while_indexing: bool = False
    skip_summarize_while_indexing: bool = False
    min_language_detection_confidence: float = 95.0
    persist_success_tasks: bool = False
    persist_retry_tasks: bool = True
    ollama_host: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}")
    tika_ocr_languages: list[TikaAllowedOcrLanguage] = ["eng"]
    tika_server_host: AnyHttpUrl = AnyHttpUrl(f"http://tika.{DOMAIN}")

    llm_model: str = "deepseek-r1:8b"
    llm_model_embedding: str = "nomic-embed-text:v1.5"
    llm_think: bool = True
    llm_temperature: float | None = None
    llm_timeout: int = 5 * 60
    llm_summarize_text_chunk_size: int = 3000
    llm_summarize_text_chunk_overlap: int = 100

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
