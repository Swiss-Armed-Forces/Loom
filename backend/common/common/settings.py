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
    bucket_name: str = "default"


class LLMClientSettings(BaseModel):
    endpoint: AnyHttpUrl = AnyHttpUrl(f"http://ollama.{DOMAIN}/v1/")
    api_key: str = "ollama"
    model: str = "huihui_ai/qwen3.5-abliterated:9b"
    temperature: float | None = None
    think: bool = False
    timeout: int = 5 * 60


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


class LLMSummarizationSettings(LLMClientSettings):
    text_chunk_size: int = 3000
    text_chunk_overlap: int = 100
    system_prompt: str = "You are an expert english summarization machine called Loom."


class LLMHydeSettings(LLMClientSettings):
    num_documents: int = 5
    temperature: float | None = 0.7


class LLMRerankSettings(LLMClientSettings):
    pass


class LLMChatSettings(LLMClientSettings):
    pass


class LLMToolSettings(LLMClientSettings):
    pass


class LLMSettings(BaseModel):
    embedding: LLMEmbeddingSettings = LLMEmbeddingSettings()
    tool: LLMToolSettings = LLMToolSettings()
    summarization: LLMSummarizationSettings = LLMSummarizationSettings()
    hyde: LLMHydeSettings = LLMHydeSettings()
    rerank: LLMRerankSettings = LLMRerankSettings()
    chat: LLMChatSettings = LLMChatSettings()


class WorkerType(StrEnum):
    WORKER = "WORKER"
    REAPER = "REAPER"
    PERSISTER = "PERSISTER"
    FLOWER = "FLOWER"
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
    celery_dead_deliver_limit: int = 3
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
    translate_host: AnyHttpUrl = AnyHttpUrl(f"http://translate.{DOMAIN}")
    translate_timeout: int = 3 * 60
    translate_startup_timeout: int = (
        10  # used only for fetching languages during app startup
    )

    imap_host: AnyUrl = AnyUrl(f"imap://dovecot.{DOMAIN}:143")
    imap_user: str = "user"
    imap_password: str = "pass"

    task_time_limit__seconds: int = 60 * 60 * 24

    roundcube_host: AnyHttpUrl = AnyHttpUrl(f"http://roundcube.{DOMAIN}")

    # SeaweedFS Configuration
    seaweedfs_master_host: AnyHttpUrl = AnyHttpUrl(
        f"http://seaweedfs-master.{DOMAIN}:9333"
    )

    random_source: bytes | None = None

    archive_enc_master_key: AESMasterKey | None = None

    automatic_indexing: bool = True

    # Indexing throttle settings
    # Max lazybytes storage before throttling new indexing
    throttle_max_lazybytes__bytes: int = 10 * (1024**3)  # 10 GB
    # Max root tasks in the repository before throttling new indexing
    throttle_max_root_tasks: int = 10_000

    # Maximum attachment recursion depth. None = unlimited.
    max_recursion_depth: int | None = None

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
