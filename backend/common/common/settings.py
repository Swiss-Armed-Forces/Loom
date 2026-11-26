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

# NOTE: ES determines upper limit for MAX_PAGE_SIZE
# (< index.max_result_window default 10000 and < search.max_buckets default 65536).
MAX_PAGE_SIZE = 10000

# What one tree-path aggregation can carry: every bucket brings a top_hits and two
# filter sub-aggregations. Both repository methods behind the browse tools clamp to it.
TREE_PATH_MAX_ELEMENT_COUNT = 50

# The widest HyDE fan-out one question may become. Every member is a serialised LLM
# call and a kNN clause of its own, so the wall-clock of a single `rag_search` is
# already the sum of them.
MAX_RAG_HYDE_DOCUMENTS = 20


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
    model: str = "qwen3.8:27b"
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
    # REMARK: No entirely happy with that parameter located here ...
    #
    # Each document is one LLM call and then one kNN clause, and both the files the
    # search may reach and the round trips it takes are multiples of it, so the cap is
    # what keeps a mistyped value from turning one question into an unbounded fan-out.
    num_documents: int = Field(default=5, ge=1, le=MAX_RAG_HYDE_DOCUMENTS)
    temperature: float | None = 0.7
    thinking: bool | None = False


class LLMRagSynthesizeSettings(LLMClientSettings):
    system_prompt: str | None = "You are an expert english chatbot called Loom."
    thinking: bool | None = True


class LLMSuggestQueriesSettings(LLMClientSettings):
    # Off for a cost reason rather than a quality one. One invocation fans out
    # `tool.suggest_queries.num_candidates` generations against an inference server that
    # answers them one at a time, so a suggestion's wall-clock is the sum of them all --
    # and each one's whole useful output is a short Lucene query string.
    thinking: bool | None = False


class LLMAgentSettings(LLMClientSettings):
    thinking: bool | None = True
    tool_timeout: int | None = 10 * 60


class LLMVisionSettings(LLMClientSettings):
    model: str = "qwen3.8:27b"
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


class LLMSystemOneSettings(BaseModel):
    """One decision model: a client that chooses rather than writes.

    Not an `LLMClientSettings`. A system-one model answers with a probability
    distribution over the members of its agent's output type and generates no text, so
    the keys below are the whole of what can reach it -- `model` through
    `common.llm.agent.build_system_one_agent`, `endpoint`/`api_key`/`timeout` through
    `common.llm.provider.build_system_one_provider`, and the last three as the model
    settings of one `POST /v1/systemone` request.

    There is no `provider`, and that is a property of the protocol rather than an
    omission: each `LLMProvider` value picks the class that shapes a *chat completion*
    for one OpenAI-compatible service, while system one has one wire format, one
    pydantic-ai provider and one model profile. Nothing is left to select between.

    What a chat client carries beyond these keys describes how text is generated
    (`thinking`, `max_tokens`, `max_sentences`, `system_prompt`, `tool_timeout`), and
    nothing here generates text. A setting that is accepted and then discarded is worse
    than one that does not exist, so they are absent rather than inherited and
    neutralised.
    """

    endpoint: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}/v1/")
    api_key: str = "ollama"
    model: str = "tev1:4b"
    timeout: int = 5 * 60
    # Scales the distribution the model answers with; the API takes it on the request
    # body. None sends none, leaving the service its own default.
    temperature: float | None = None
    extra_headers: LLMExtraHeaders | None = None
    extra_body: LLMExtraBody | None = None


class LLMSystemOneClientsSettings(BaseModel):
    """The decision models, one entry per question a system-one model answers.

    Its own group rather than entries in `LLMSettings`, because a decision model takes
    a different set of keys from a chat client; one entry per use case rather than one
    shared block, because the questions are asked of different texts and are worth
    pointing and tuning apart.

    Every entry always names a model. Switching a use case off is a separate decision
    from pointing it at a service, and it is made where the rest of the pipeline's
    switches are -- `pipeline.skip_ocr_language_detection_while_indexing` for the OCR
    question, and `pipeline.skip_translate_while_indexing` for the translation one,
    which switches translation off wholesale. A client that is reachable but never
    asked and a client that is asked but unreachable are different states, and one key
    cannot mean both.
    """

    rag_rerank: LLMSystemOneSettings = LLMSystemOneSettings()
    translation_language_detection: LLMSystemOneSettings = LLMSystemOneSettings()
    ocr_language_detection: LLMSystemOneSettings = LLMSystemOneSettings()
    index_prioritization: LLMSystemOneSettings = LLMSystemOneSettings()


class SuggestQueriesToolSettings(BaseModel):
    # One candidate per `worker.ai.tasks.suggest_queries_tool.QueryStrategy` member.
    # Every candidate is a chat generation the inference server answers on its own, and
    # the chord's callback waits for the last of them, so the count is the multiplier on
    # a suggestion's wall-clock. Raising it past the strategy count buys repeated
    # strategies separated by their seed alone, which are the candidates likeliest to
    # produce the same query string and collapse in the aggregation.
    num_candidates: int = 5
    max_results: int = 3


class ExecuteQueryToolSettings(BaseModel):
    """Settings for the execute_query AI tool.

    Attributes:
        page_size: Files returned per page.
    """

    page_size: int = Field(default=10, ge=1, le=MAX_PAGE_SIZE)


class BrowseToolsSettings(BaseModel):
    """Settings shared by the list_folder_contents and search_by_filename AI tools.

    Attributes:
        page_size: Entries returned per page.  Bounded by what one tree-path
            aggregation can carry, which is also what both repository methods behind
            these tools clamp to — a larger value would be silently cut down.
    """

    page_size: int = Field(
        default=TREE_PATH_MAX_ELEMENT_COUNT, ge=1, le=TREE_PATH_MAX_ELEMENT_COUNT
    )


class RagSearchToolSettings(BaseModel):
    """Settings for the rag_search AI tool.

    Attributes:
        files_per_probe: How many files one kNN probe may reach, which also sets the
            depth each shard explores. Tuned rather than derived: it trades the breadth
            of the corpus considered against the Elasticsearch work of one clause, and
            how many files are worth looking at is a property of the corpus.
        max_chunks_for_reranking: How many chunks reach the reranker, which spends one
            LLM call on each against an inference server that answers them one at a
            time. The chunks fetched per file derive from this and `files_per_probe`
            together, so raising it widens retrieval as well as the rerank budget.
    """

    files_per_probe: int = Field(default=7, ge=1)
    max_chunks_for_reranking: int = Field(default=20, ge=1)


class ToolSettings(BaseModel):
    suggest_queries: SuggestQueriesToolSettings = SuggestQueriesToolSettings()
    execute_query: ExecuteQueryToolSettings = ExecuteQueryToolSettings()
    browse: BrowseToolsSettings = BrowseToolsSettings()
    rag_search: RagSearchToolSettings = RagSearchToolSettings()


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
    # NOTE: Due to a suspected Celery bug, tasks get stuck on the worker when concurrency
    # is scaled dynamically — they are accepted but never executed. Until this is
    # understood and fixed, scaling is disabled by enforcing a fixed concurrency.
    worker_concurrency: int = 4
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

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:31143")
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

    # Depth at which attachment extraction stops. 0 extracts no attachments.
    indexing_max_recursion_depth: int = 0

    # Maximum number of times a lost file is reindexed before the sweep gives up on it
    # and marks it failed.
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
    llm_system_one: LLMSystemOneClientsSettings = LLMSystemOneClientsSettings()


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
