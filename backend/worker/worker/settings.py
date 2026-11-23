import json
import logging
from enum import StrEnum
from typing import Annotated, Any, Literal

from common.settings import DOMAIN
from common.settings import Settings as CommonSettings
from gotenberg_client.options import Measurement, MeasurementUnitType, PageSize
from pydantic import AnyHttpUrl, field_validator
from pydantic_ai import UseEnumMemberDocstrings
from pydantic_settings import NoDecode

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


# The widely written languages tesseract has traineddata for, as the options a decision
# model picks between. A subset of `TikaAllowedOcrLanguage`, because the answer is
# appended straight into the `X-Tika-OCRLanguage` header -- the one exception being
# `other`, which means no header entry at all. `test_tika_service.py` holds the two
# lists to that relation.
#
# The class docstring is the question the service is asked, and the member docstrings
# are the descriptions of its options, so both hold what the model should read and
# nothing else.
class TikaCommonOcrLanguage(UseEnumMemberDocstrings, StrEnum):
    """Which language is the content of this file likely written in?"""

    # spellchecker:off
    ENG = "eng"
    """The content is written in English."""

    CHI_SIM = "chi_sim"
    """The content is written in Simplified Chinese."""

    HIN = "hin"
    """The content is written in Hindi."""

    SPA = "spa"
    """The content is written in Spanish."""

    ARA = "ara"
    """The content is written in Arabic."""

    FRA = "fra"
    """The content is written in French."""

    BEN = "ben"
    """The content is written in Bengali."""

    POR = "por"
    """The content is written in Portuguese."""

    IND = "ind"
    """The content is written in Indonesian."""

    URD = "urd"
    """The content is written in Urdu."""

    RUS = "rus"
    """The content is written in Russian."""

    DEU = "deu"
    """The content is written in German."""

    JPN = "jpn"
    """The content is written in Japanese."""

    MAR = "mar"
    """The content is written in Marathi."""

    VIE = "vie"
    """The content is written in Vietnamese."""

    TEL = "tel"
    """The content is written in Telugu."""

    SWA = "swa"
    """The content is written in Swahili."""

    TUR = "tur"
    """The content is written in Turkish."""

    PAN = "pan"
    """The content is written in Punjabi."""

    TGL = "tgl"
    """The content is written in Tagalog."""

    OTHER = "other"
    """The name carries no language signal, or names a language not listed above."""

    # spellchecker:on


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
    skip_image_description_while_indexing: bool = True
    skip_embedding_while_indexing: bool = False
    skip_auto_tag_file_while_indexing: bool = False
    # Heads the tika chain, retries on a transient failure and degrades only once the
    # budget is spent, so a deployment with no inference service behind it pays
    # TIKA_MAX_RETRIES backed-off calls per image and PDF for a hint it cannot get.
    # This is how such a deployment declines to ask; the OCR itself still runs, with
    # `tika_ocr_languages` alone.
    skip_ocr_language_detection_while_indexing: bool = False
    min_language_detection_confidence: float = 95.0
    # Lower than its generative sibling because the two numbers are not comparable: a
    # decision model reports a calibrated distribution over the members of
    # `LanguagesToDetect`, so 75% of the mass on one language is a firm answer, while a
    # generated confidence is a number the model wrote down. What is behind the gate is
    # the same either way -- a
    # detected language puts the file through `translate_task`, which is one LLM call
    # per 2000 characters, per language -- so raise this rather than lower it.
    min_language_detection_system_one_confidence: float = 75.0
    persist_success_tasks: bool = True
    persist_retry_tasks: bool = True
    max_no_of_persisted_succeeded_tasks: int = 2
    max_no_of_persisted_retried_tasks: int = 2
    max_no_of_persisted_failed_tasks: int = 2
    tika_ocr_languages: Annotated[list[TikaAllowedOcrLanguage], NoDecode] = [
        "eng",
        "deu",
        "fra",
    ]
    tika_server_host: AnyHttpUrl = AnyHttpUrl(f"http://tika.{DOMAIN}")

    rspam_host: AnyHttpUrl = AnyHttpUrl(f"http://rspamd-worker.{DOMAIN}")

    summary_max_chunks: int = 5
    uploaded_files_days_before_hidden: int | None = None
    imap_folder_days_before_unsubscribe: int | None = None
    reindex_lost_files_max_files: int = 100
    flush_file_storage_service_max_objects: int = 1000

    llm_chat_message_history_index: str = "message_history"

    auto_tag_file_similarity_threshold: float = 0.95

    gotenberg_host: AnyHttpUrl = AnyHttpUrl(f"http://gotenberg.{DOMAIN}")
    tika_timeout_seconds: int = 5 * 60
    imagemagick_timeout_seconds: int = 10 * 60
    gotenberg_timeout_seconds: int = 1 * 60

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

    heartbeat_file_name: str = "/tmp/beat_heartbeat"

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
