import logging
import os
from enum import StrEnum
from pathlib import Path
from socket import gethostname

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    AnyWebsocketUrl,
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.environment import get_loglevel, is_development_env
from common.services.encryption_service import AESMasterKey

logger = logging.getLogger(__name__)

CELERY_QUEUE_NAME_MAXLEN = 255


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
    host: str = f"s3.{DOMAIN}"
    secret_key: str | None = None
    access_key: str | None = None
    secure_connection: bool = False
    connection_pool_size: int = 64


class FileStorageSettings(S3StorageSettings):
    bucket_name: str = "loom-filestorage"


class LazybytesStorageSettings(S3StorageSettings):
    bucket_name: str = "loom-lazybytes"


class IntakeS3StorageSettings(S3StorageSettings):
    bucket_name: str = "loom-intake"


LLMExtraHeaders = dict[str, str]
LLMExtraBody = dict[str, object]


class LLMProvider(StrEnum):
    """Which service answers at ``endpoint``.

    One value per service, each backed by one class in ``common.llm.provider`` -- that
    module is where a service's quirks are written down, and where the model family is
    matched off the name in ``model``.
    """

    # Ollama, spoken to directly.
    OLLAMA = "ollama"
    # LiteLLM proxy; in Loom's deployments it fronts vLLM.
    LITELLM = "litellm"
    # Infomaniak's OpenAI-compatible AI service.
    INFOMANIAK = "infomaniak"
    # Hosted OpenAI, or a gateway matching its behaviour exactly.
    OPENAI = "openai"


class LLMClientSettings(BaseModel):
    provider: LLMProvider = LLMProvider.OLLAMA
    endpoint: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}/v1/")
    api_key: str = "ollama"
    model: str = "huihui_ai/qwen3.5-abliterated:9b"
    temperature: float | None = None
    # None sends no reasoning_effort at all, leaving the model to its own default.
    thinking: bool | None = None
    timeout: int = 5 * 60
    # NOTE: max_tokens can not exceed context window length of model
    max_tokens: int | None = 128000
    max_sentences: int | None = None
    extra_headers: LLMExtraHeaders | None = None
    extra_body: LLMExtraBody | None = None
    system_prompt: str | None = None
    tool_timeout: int | None = None


class LLMEmbeddingSettings(LLMClientSettings):
    model: str = "nomic-embed-text-v2-moe"
    dimensions: int = (
        # Note: 4096 is largest vector supported by ElasticSearch
        768  # -> nomic-embed-text-v2-moe
    )
    text_chunk_size: int = 400
    text_chunk_overlap: int = 50
    document_prefix: str = "search_document:"
    query_prefix: str = "search_query:"
    # NOTE: no `thinking` override. The embedding path is `build_embedder`, which reads
    # `extra_headers`/`extra_body` only -- pydantic-ai's `EmbeddingSettings` has no
    # thinking key, and the embeddings API has no reasoning to switch off. The inherited
    # `None` says that by omission; a `False` here would read as a setting that works.


class LLMSummarizationBaseSettings(LLMClientSettings):
    system_prompt: str | None = "You are an expert summarization machine called Loom."
    max_sentences: int | None = 30


class LLMSummarizationKeyPointsSettings(LLMSummarizationBaseSettings):
    text_chunk_size: int = 3000
    text_chunk_overlap: int = 100
    max_sentences: int | None = 10
    thinking: bool | None = False


class LLMSummarizationSettings(LLMSummarizationBaseSettings):
    thinking: bool | None = True


class LLMSummarizationRefineSettings(LLMSummarizationBaseSettings):
    thinking: bool | None = True
    max_sentences: int | None = 30


class LLMRagHydeSettings(LLMClientSettings):
    num_documents: int = (
        5  # REMARK: No entirely happy with that parameter located here ...
    )
    temperature: float | None = 0.7
    thinking: bool | None = False


class LLMRagRerankSettings(LLMClientSettings):
    system_prompt: str | None = "You are an expert reranking machine called Loom."
    # Off deliberately. `rerank_and_synthesize` fans out one call per chunk, capped at
    # MAX_SCORED_SEARCH_EMBEDDINGS_FOR_RERANKING (50), against an inference server that
    # serves them one at a time -- so a question's rerank wall-clock is the sum of all
    # 50 generations, and the whole useful output is a single integer score.
    thinking: bool | None = False
    # The answer is one number, so the inherited 128000 caps nothing that matters while
    # letting a single runaway generation eat the 5-minute `timeout` -- which `rerank`
    # then retries up to RAG_MAX_RETRIES times, on an already saturated queue.
    max_tokens: int | None = 512


class LLMRagSynthesizeSettings(LLMClientSettings):
    system_prompt: str | None = "You are an expert english chatbot called Loom."
    thinking: bool | None = True


class LLMSuggestQueriesSettings(LLMClientSettings):
    # Off for the same cost reason as `rag_rerank`. One invocation fans out
    # `tool.suggest_queries.num_candidates` (10) generations against an inference server
    # that answers them one at a time, so a suggestion's wall-clock is the sum of all
    # ten -- and each one's whole useful output is a short Lucene query string.
    thinking: bool | None = False


class LLMAgentSettings(LLMClientSettings):
    thinking: bool | None = True
    tool_timeout: int | None = 10 * 60


class LLMVisionSettings(LLMClientSettings):
    model: str = "huihui_ai/qwen3.5-abliterated:9b"
    system_prompt: str | None = "You are an expert at analysing what's in an image"
    max_sentences: int | None = 20
    thinking: bool | None = False


class LLMLanguageDetectionSettings(LLMClientSettings):
    system_prompt: str | None = "You are a language detection service."
    thinking: bool | None = False


class LLMTranslationSettings(LLMClientSettings):
    system_prompt: str | None = """
You are a translation service.
Output only the translated text.
No explanations, no preamble, no commentary.
"""
    thinking: bool | None = False


class SuggestQueriesToolSettings(BaseModel):
    num_candidates: int = 10
    max_results: int = 3


class ToolSettings(BaseModel):
    suggest_queries: SuggestQueriesToolSettings = SuggestQueriesToolSettings()


class LLMSettings(BaseModel):
    embedding: LLMEmbeddingSettings = LLMEmbeddingSettings()
    suggest_queries: LLMSuggestQueriesSettings = LLMSuggestQueriesSettings()
    agent: LLMAgentSettings = LLMAgentSettings()
    summarization_key_points: LLMSummarizationKeyPointsSettings = (
        LLMSummarizationKeyPointsSettings()
    )
    summarization: LLMSummarizationSettings = LLMSummarizationSettings()
    summarization_refine: LLMSummarizationRefineSettings = (
        LLMSummarizationRefineSettings()
    )
    rag_hyde: LLMRagHydeSettings = LLMRagHydeSettings()
    rag_rerank: LLMRagRerankSettings = LLMRagRerankSettings()
    rag_synthesize: LLMRagSynthesizeSettings = LLMRagSynthesizeSettings()
    vision: LLMVisionSettings = LLMVisionSettings()
    language_detection: LLMLanguageDetectionSettings = LLMLanguageDetectionSettings()
    translation: LLMTranslationSettings = LLMTranslationSettings()


class WorkerType(StrEnum):
    WORKER = "WORKER"
    REAPER = "REAPER"
    PERSISTER = "PERSISTER"
    BEAT = "BEAT"
    INSPECT = "INSPECT"


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

    worker_type: WorkerType = WorkerType.INSPECT
    worker_max_concurrency: int = 4
    # NOTE: worker_min_concurrency MUST equal worker_max_concurrency (no scaling allowed).
    # Due to a suspected Celery bug, tasks get stuck on the worker when concurrency
    # is scaled dynamically — they are accepted but never executed. Until this is
    # understood and fixed, scaling is disabled by enforcing a fixed concurrency.
    worker_min_concurrency: int = 4
    num_persister_shards: int = 16
    persister_total: int = 1  # Total number of PERSISTER workers
    persister_id: int = Field(default_factory=_get_persister_id_from_hostname)

    es_host: AnyHttpUrl = AnyHttpUrl(f"http://elasticsearch.{DOMAIN}")
    es_timeout: int = 120
    es_number_of_shards: int = 1
    es_number_of_replicas: int = 0
    rabbit_mq_management_host: AnyHttpUrl = AnyHttpUrl(
        f"http://guest:guest@rabbit.{DOMAIN}"
    )
    celery_broker_host: AnyUrl = AnyUrl(f"amqp://rabbit-amqp.{DOMAIN}")
    celery_backend_host: AnyUrl = AnyUrl(f"redis://redis.{DOMAIN}:6379/0?protocol=3")
    celery_queue_name_prefix: str = "loom:"
    celery_deliver_limit: int = 5
    celery_graveyard_deliver_limit: int = 3
    celery_default_task_name: str = "default"
    celery_graveyard_task_name: str = "graveyard"
    celery_dead_task_name: str = "dead"
    celery_dead_deliver_limit: int = 1
    celery_abyss_task_name: str = "abyss"
    celery_abyss_ttl__seconds: int = 7 * 24 * 60 * 60  # 7 days
    celery_persister_shard_prefix: str = "persister.shard"
    celery_unroutable_ttl__seconds: int = 24 * 60 * 60
    celery_unroutable_task_name: str = "unroutable"
    celery_default_exchange_name: str = "loom"
    celery_default_exchange_type: str = "topic"
    celery_alternate_exchange_name: str = "ae-loom"

    redis_cache_host: AnyUrl = AnyUrl(f"redis://redis-cache.{DOMAIN}:6380/0?protocol=3")
    lazy_threshold_bytes: int = 1024  # 1KiB

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:143")
    imap_user: str = "user"
    imap_password: str = "pass"

    task_time_limit_seconds: int = 60 * 60 * 24

    # SeaweedFS Configuration
    seaweedfs_master_host: AnyHttpUrl = AnyHttpUrl(
        f"http://seaweedfs-master.{DOMAIN}:9333"
    )

    random_source: bytes | None = None

    archive_enc_master_key: AESMasterKey | None = None

    # Indexing throttle settings
    # Max lazybytes storage before throttling new indexing
    throttle_max_lazybytes__bytes: int = 10 * (1024**3)  # 10 GB

    # Maximum attachment recursion depth. None = unlimited.
    max_recursion_depth: int | None = None

    # Maximum number of times a lost file is reindexed before giving up.
    max_reindex_count: int = 2

    # Memory watermark for memory pressure detection
    # E.g., 0.9 means memory pressure when container uses 90% of memory limit
    memory_watermark_percent: float = 0.9

    @field_validator("archive_enc_master_key", mode="before")
    @classmethod
    def parse_archive_enc_master_key(cls, value: str) -> AESMasterKey:
        if isinstance(value, str):
            return AESMasterKey.from_string(value)
        logger.warning("No archive encryption master key provided. Using fixed key.")
        return AESMasterKey.from_fixed_key()

    @model_validator(mode="after")
    def validate_worker_concurrency(self) -> "Settings":
        if self.worker_min_concurrency > self.worker_max_concurrency:
            raise ValueError(
                f"worker_min_concurrency ({self.worker_min_concurrency}) must be equal or"
                f"less than worker_max_concurrency ({self.worker_max_concurrency})"
            )
        if self.worker_min_concurrency != self.worker_max_concurrency:
            raise ValueError(
                f"worker_min_concurrency ({self.worker_min_concurrency}) must equal "
                f"worker_max_concurrency ({self.worker_max_concurrency}): dynamic "
                f"concurrency scaling is disabled due to a suspected Celery bug that "
                f"causes tasks to get stuck when the worker pool is scaled"
            )
        return self

    @model_validator(mode="after")
    def adjust_lazy_threshold_for_reaper(self) -> "Settings":
        if self.worker_type == WorkerType.REAPER:
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

    file_storage: FileStorageSettings = FileStorageSettings()
    lazybytes_storage: LazybytesStorageSettings = LazybytesStorageSettings()
    intake_storage: IntakeS3StorageSettings = IntakeS3StorageSettings()

    tool: ToolSettings = ToolSettings()
    llm: LLMSettings = LLMSettings()


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
