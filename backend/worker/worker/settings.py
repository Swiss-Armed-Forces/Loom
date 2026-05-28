import json
import logging
from typing import Any, Literal

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from gotenberg_client.options import Measurement, MeasurementUnitType, PageSize
from pydantic import AnyHttpUrl, field_validator

logger = logging.getLogger(__name__)

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

    @field_validator("tika_ocr_languages", mode="before")
    @classmethod
    def _parse_tika_ocr_languages(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",") if lang.strip()]
        return v

    skip_translate_while_indexing: bool = True
    skip_summarize_while_indexing: bool = True
    skip_embedding_while_indexing: bool = False
    skip_auto_tag_file_while_indexing: bool = False
    min_language_detection_confidence: float = 95.0
    persist_success_tasks: bool = False
    persist_retry_tasks: bool = True
    tika_ocr_languages: list[TikaAllowedOcrLanguage] = ["eng", "deu", "fra"]
    tika_server_host: AnyHttpUrl = AnyHttpUrl(f"http://tika.{DOMAIN}")

    rspam_host: AnyHttpUrl = AnyHttpUrl(f"http://rspamd-worker.{DOMAIN}")

    summary_max_chunks: int = 5
    uploaded_files_days_before_hidden: int | None = None
    imap_folder_days_before_unsubscribe: int | None = None

    llm_rerank_system_prompt: str = (
        """You are an expert reranking machine called Loom."""
    )

    llm_chat_system_prompt: str = """You are an expert english chatbot called Loom"""
    llm_chat_message_history_index: str = "message_history"

    auto_tag_file_similarity_threshold: float = 0.75

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

    # SeaweedFS Maintenance Settings
    seaweedfs_shell_timeout: int = int(60 * 60 * 1.5)  # 1.5 hour(s)

    # Persister timing settings
    persister_debounce_window: float = 2.5  # seconds to wait for more mutations
    persister_max_delay: float = 5  # max seconds before forced flush
    persister_max_delay_forget_multiplier: int = (
        10  # multiplier for stale object eviction
    )
    persister_save_max_retries: int = 3  # max conflict retries before giving up
    persister_memory_pressure_timeout: float = (
        60.0  # seconds before terminating under memory pressure
    )

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

logger.debug(
    "Effective settings:\n%s",
    json.dumps(settings.model_dump(), indent=2, default=str),
)
