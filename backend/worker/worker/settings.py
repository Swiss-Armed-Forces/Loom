from datetime import timedelta
from typing import Any, Literal, Tuple, Type

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from gotenberg_client.options import Measurement, MeasurementUnitType, PageSize
from pydantic import AnyHttpUrl
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class SettingsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "tika_ocr_languages":
            if value:
                return list(value.split(","))
        return value


# from https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
TikaAllowedOcrLanguage = Literal[
    # spellchecker:off
    "afr",
    "ara",
    "asm",
    "aze",
    "aze_cyrl",
    "bel",
    "ben",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ceb",
    "ces",
    "chi_sim",
    "chi_tra",
    "chr",
    "cos",
    "cym",
    "dan",
    "dan_frak",
    "deu",
    "deu_frak",
    "dzo",
    "ell",
    "eng",
    "enm",
    "epo",
    "equ",
    "est",
    "eus",
    "fao",
    "fas",
    "fil",
    "fin",
    "fra",
    "frk",
    "frm",
    "fry",
    "gla",
    "gle",
    "glg",
    "grc",
    "guj",
    "hat",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "iku",
    "ind",
    "isl",
    "ita",
    "ita_old",
    "jav",
    "jpn",
    "kan",
    "kat",
    "kat_old",
    "kaz",
    "khm",
    "kir",
    "kmr",
    "kor",
    "kor_vert",
    "kur",
    "lao",
    "lat",
    "lav",
    "lit",
    "ltz",
    "mal",
    "mar",
    "mkd",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "oci",
    "ori",
    "osd",
    "pan",
    "pol",
    "por",
    "pus",
    "que",
    "ron",
    "rus",
    "san",
    "sin",
    "slk",
    "slk_frak",
    "slv",
    "snd",
    "spa",
    "spa_old",
    "sqi",
    "srp",
    "srp_latn",
    "sun",
    "swa",
    "swe",
    "syr",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tgl",
    "tha",
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "uzb_cyrl",
    "vie",
    "yid",
    "yor",
    # spellchecker:on
]


class Settings(CommonSettings):
    """All settings for the worker service."""

    # pylint: disable=too-many-arguments, too-many-positional-arguments
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

    gotenberg_host: AnyHttpUrl = AnyHttpUrl(f"http://gotenberg.{DOMAIN}")
    gotenberg_timeout: int = 1 * 60

    thumbnail_width: int = 300
    thumbnail_height: int = 200
    thumbnail_max_frames_montage: int = 6  # must be > 1

    rendered_image_resolution: int = 300
    rendered_image_width: int = 1200
    rendered_image_smush_offset: int = 100
    rendered_pdf_page_width__mm: int = 210  # A4
    rendered_pdf_page_height__mm: int = 297  # A4

    @property
    def rendered_pdf_page_size(self) -> PageSize:
        return PageSize(
            width=Measurement(
                unit=MeasurementUnitType.Millimeters,
                value=self.rendered_pdf_page_width__mm,
            ),
            height=Measurement(
                unit=MeasurementUnitType.Millimeters,
                value=self.rendered_pdf_page_height__mm,
            ),
        )


settings = Settings()
