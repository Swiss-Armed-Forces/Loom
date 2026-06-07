import logging
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import urllib3
from celery import Celery
from elasticsearch import Elasticsearch
from libretranslatepy import LibreTranslateAPI
from minio import Minio
from openai import OpenAI
from redis import StrictRedis
from redis.asyncio import StrictRedis as StrictRedisAsync

from common.ai_context.ai_context_repository import AiContextRepository
from common.ai_context.ai_scheduling_service import AiSchedulingService
from common.archive.archive_encryption_service import ArchiveEncryptionService
from common.archive.archive_repository import ArchiveRepository
from common.archive.archive_scheduling_service import ArchiveSchedulingService
from common.celery_app import BaseTask, init_celery_app
from common.elasticsearch import init_elasticsearch
from common.file.file_repository import FileRepository
from common.file.file_scheduling_service import FileSchedulingService
from common.messages.pubsub_service import PubSubService
from common.services.celery_inspect_service import CeleryInspectService
from common.services.imap_service import IMAPService
from common.services.lazybytes_service import (
    FileStorageLazyBytesService,
    TempLazyBytesService,
)
from common.services.query_builder import QueryBuilder
from common.services.queues_service import QueuesService
from common.services.task_scheduling_service import TaskSchedulingService
from common.services.wipe_service import WipeService
from common.settings import settings
from common.task_object.root_task_information_repository import (
    RootTaskInformationRepository,
)
from common.utils.noop_decorator import noop_decorator


class DependencyException(Exception):
    pass


# Note, "= None" assignments are needed here to make flake8 happy
_libretranslate_api: LibreTranslateAPI | None = None
_query_builder: QueryBuilder | None = None
_redis_client: StrictRedis | None = None
_redis_client_async: StrictRedisAsync | None = None
_redis_cache_client: StrictRedis | None = None
_pubsub_service: PubSubService | None = None
_elasticsearch: Elasticsearch | None = None
_file_storage_service: FileStorageLazyBytesService | None = None
_root_task_information_repository: RootTaskInformationRepository | None = None
_lazybytes_service: TempLazyBytesService | None = None
_imap_service: IMAPService | None = None
_s3_intake_client: Minio | None = None
_celery_app: Optional["Celery[BaseTask]"] = None
_queues_service: QueuesService | None = None
_archive_repository: ArchiveRepository | None = None
_file_repository: FileRepository | None = None
_ai_context_repository: AiContextRepository | None = None
_task_scheduling_service: TaskSchedulingService | None = None
_file_scheduling_service: FileSchedulingService | None = None
_archive_scheduling_service: ArchiveSchedulingService | None = None
_ai_scheduling_service: AiSchedulingService | None = None
_archive_encryption_service: ArchiveEncryptionService | None = None
_llm_summarization_client: OpenAI | None = None
_llm_hyde_client: OpenAI | None = None
_llm_rerank_client: OpenAI | None = None
_llm_chat_client: OpenAI | None = None
_llm_embedding_client: OpenAI | None = None
_llm_tool_client: OpenAI | None = None
_llm_vision_client: OpenAI | None = None
_celery_inspect_service: CeleryInspectService | None = None
_wipe_service: WipeService | None = None


logger = logging.getLogger(__name__)


# pylint: disable=too-many-statements
def init(init_elasticsearch_documents: bool = False):
    # pylint: disable=global-statement
    logger.info("Initialize common dependencies")

    # NOTE: We do NOT close inherited connections before reinitializing.
    # After fork(), the child has copies of the parent's connection objects
    # sharing the same underlying sockets. Calling close() in the child
    # could affect the parent's connections.
    #
    # Instead, we simply overwrite the globals with fresh connections.
    # The orphaned connection objects in the child will be cleaned up
    # when the subprocess exits.

    global _libretranslate_api
    _libretranslate_api = LibreTranslateAPI(str(settings.translate_host))

    global _query_builder
    _query_builder = QueryBuilder(_libretranslate_api)

    global _redis_client
    _redis_client = StrictRedis.from_url(str(settings.celery_backend_host))

    global _redis_client_async
    _redis_client_async = StrictRedisAsync.from_url(str(settings.celery_backend_host))

    global _redis_cache_client
    _redis_cache_client = StrictRedis.from_url(str(settings.redis_cache_host))

    global _pubsub_service
    _pubsub_service = PubSubService(_redis_client, _redis_client_async)

    global _elasticsearch
    _elasticsearch = init_elasticsearch(
        _query_builder,
        _pubsub_service,
        init_elasticsearch_documents,
    )

    global _file_storage_service
    _file_storage_service = FileStorageLazyBytesService(
        Minio(
            settings.file_storage.host,
            settings.file_storage.access_key,
            settings.file_storage.secret_key,
            secure=settings.file_storage.secure_connection,
            http_client=urllib3.PoolManager(
                maxsize=settings.file_storage.connection_pool_size
            ),
        ),
        settings.file_storage.bucket_name,
        # We always want to store data in the file storage service, to
        # avoid embedded data in ElasticSearch
        threshold_bytes=-1,
    )

    global _root_task_information_repository
    _root_task_information_repository = RootTaskInformationRepository(
        _query_builder, _pubsub_service
    )

    global _lazybytes_service
    _lazybytes_service = TempLazyBytesService(
        Minio(
            settings.lazybytes_storage.host,
            settings.lazybytes_storage.access_key,
            settings.lazybytes_storage.secret_key,
            secure=settings.lazybytes_storage.secure_connection,
            http_client=urllib3.PoolManager(
                maxsize=settings.lazybytes_storage.connection_pool_size
            ),
        ),
        settings.lazybytes_storage.bucket_name,
        threshold_bytes=settings.lazy_threshold_bytes,
    )

    global _imap_service
    _imap_service = IMAPService(
        settings.imap_host, settings.imap_user, settings.imap_password
    )

    global _s3_intake_client
    _s3_intake_client = Minio(
        settings.intake_storage.host,
        access_key=settings.intake_storage.access_key,
        secret_key=settings.intake_storage.secret_key,
        secure=settings.intake_storage.secure_connection,
        http_client=urllib3.PoolManager(
            maxsize=settings.intake_storage.connection_pool_size
        ),
    )

    # NOTE: _celery_app must only be initialized once. init_celery_app() calls
    # app.set_current() and app.set_default(), which would replace the global/thread-local
    # Celery app reference in forked subprocesses with a new app that lacks registered tasks,
    # breaking task dispatch. The "init once" guard ensures it is never replaced.
    global _celery_app
    if _celery_app is None or isinstance(_celery_app, MagicMock):
        _celery_app = init_celery_app()

    global _queues_service
    _queues_service = QueuesService(str(settings.rabbit_mq_management_host))

    global _archive_repository
    _archive_repository = ArchiveRepository(_query_builder, _pubsub_service)

    global _file_repository
    _file_repository = FileRepository(_query_builder, _pubsub_service)

    global _ai_context_repository
    _ai_context_repository = AiContextRepository(_query_builder, _pubsub_service)

    global _task_scheduling_service
    _task_scheduling_service = TaskSchedulingService(
        _celery_app,
        _root_task_information_repository,
    )

    global _file_scheduling_service
    _file_scheduling_service = FileSchedulingService(
        _file_repository,
        _file_storage_service,
        _task_scheduling_service,
        _lazybytes_service,
    )

    global _archive_scheduling_service
    _archive_scheduling_service = ArchiveSchedulingService(
        _archive_repository,
        _task_scheduling_service,
    )

    global _ai_scheduling_service
    _ai_scheduling_service = AiSchedulingService(
        _ai_context_repository,
        _task_scheduling_service,
    )

    global _archive_encryption_service
    _archive_encryption_service = ArchiveEncryptionService(
        settings.archive_enc_master_key
    )

    global _llm_summarization_client
    _llm_summarization_client = OpenAI(
        base_url=str(settings.llm.summarization.endpoint),
        api_key=settings.llm.summarization.api_key,
        timeout=settings.llm.summarization.timeout,
    )

    global _llm_hyde_client
    _llm_hyde_client = OpenAI(
        base_url=str(settings.llm.hyde.endpoint),
        api_key=settings.llm.hyde.api_key,
        timeout=settings.llm.hyde.timeout,
    )

    global _llm_rerank_client
    _llm_rerank_client = OpenAI(
        base_url=str(settings.llm.rerank.endpoint),
        api_key=settings.llm.rerank.api_key,
        timeout=settings.llm.rerank.timeout,
    )

    global _llm_chat_client
    _llm_chat_client = OpenAI(
        base_url=str(settings.llm.chat.endpoint),
        api_key=settings.llm.chat.api_key,
        timeout=settings.llm.chat.timeout,
    )

    global _llm_embedding_client
    _llm_embedding_client = OpenAI(
        base_url=str(settings.llm.embedding.endpoint),
        api_key=settings.llm.embedding.api_key,
        timeout=settings.llm.embedding.timeout,
    )

    global _llm_tool_client
    _llm_tool_client = OpenAI(
        base_url=str(settings.llm.tool.endpoint),
        api_key=settings.llm.tool.api_key,
        timeout=settings.llm.tool.timeout,
    )

    global _llm_vision_client
    _llm_vision_client = OpenAI(
        base_url=str(settings.llm.vision.endpoint),
        api_key=settings.llm.vision.api_key,
        timeout=settings.llm.vision.timeout,
    )

    global _celery_inspect_service
    _celery_inspect_service = CeleryInspectService(
        _celery_app, _queues_service, _redis_client
    )

    global _wipe_service
    _wipe_service = WipeService(
        celery_app=_celery_app,
        elasticsearch=_elasticsearch,
        query_builder=_query_builder,
        pubsub_service=_pubsub_service,
        redis_client=_redis_client,
        redis_cache_client=_redis_cache_client,
        s3_intake_client=_s3_intake_client,
        file_storage_service=_file_storage_service,
        lazybytes_service=_lazybytes_service,
        imap_service=_imap_service,
        celery_inspect_service=_celery_inspect_service,
        queues_service=_queues_service,
    )


# pylint: disable=too-many-statements
def mock_init():
    # pylint: disable=global-statement
    logger.info("Initialize global mock dependencies")

    global _libretranslate_api
    _libretranslate_api = MagicMock(spec=LibreTranslateAPI)

    global _query_builder
    _query_builder = MagicMock(spec=QueryBuilder)

    global _redis_client
    _redis_client = MagicMock(spec=StrictRedis)

    global _redis_client_async
    _redis_client_async = AsyncMock(spec=StrictRedisAsync)

    global _redis_cache_client
    _redis_cache_client = MagicMock(spec=StrictRedis)

    global _pubsub_service
    _pubsub_service = MagicMock(spec=PubSubService)

    global _elasticsearch
    _elasticsearch = MagicMock(spec=Elasticsearch)

    global _file_storage_service
    _file_storage_service = MagicMock(spec=FileStorageLazyBytesService)

    global _root_task_information_repository
    _root_task_information_repository = MagicMock(spec=RootTaskInformationRepository)

    global _lazybytes_service
    _lazybytes_service = MagicMock(spec=TempLazyBytesService)

    global _imap_service
    _imap_service = MagicMock(spec=IMAPService)

    global _s3_intake_client
    _s3_intake_client = MagicMock(spec=Minio)

    global _celery_app
    _celery_app = MagicMock(spec=Celery)
    # make the task decorator work: needed if we want to tests tasks
    _celery_app.task = noop_decorator

    global _queues_service
    _queues_service = MagicMock(spec=QueuesService)

    global _archive_repository
    _archive_repository = MagicMock(spec=ArchiveRepository)

    global _file_repository
    _file_repository = MagicMock(spec=FileRepository)

    global _ai_context_repository
    _ai_context_repository = MagicMock(spec=AiContextRepository)

    global _task_scheduling_service
    _task_scheduling_service = MagicMock(spec=TaskSchedulingService)

    global _file_scheduling_service
    _file_scheduling_service = MagicMock(spec=FileSchedulingService)

    global _archive_scheduling_service
    _archive_scheduling_service = MagicMock(spec=ArchiveSchedulingService)

    global _ai_scheduling_service
    _ai_scheduling_service = MagicMock(spec=AiSchedulingService)

    global _archive_encryption_service
    _archive_encryption_service = MagicMock(spec=ArchiveEncryptionService)

    # OpenAI's sub-clients (chat, embeddings, ...) are set on the instance in
    # __init__, not as class attributes, so `MagicMock(spec=OpenAI)` rejects them.
    # Spec against a real instance instead -- no network calls happen at
    # construction, the dummy api_key is just stored.
    openai_spec = OpenAI(api_key="test")

    global _llm_summarization_client
    _llm_summarization_client = MagicMock(spec=openai_spec)

    global _llm_hyde_client
    _llm_hyde_client = MagicMock(spec=openai_spec)

    global _llm_rerank_client
    _llm_rerank_client = MagicMock(spec=openai_spec)

    global _llm_chat_client
    _llm_chat_client = MagicMock(spec=openai_spec)

    global _llm_embedding_client
    _llm_embedding_client = MagicMock(spec=openai_spec)

    global _llm_tool_client
    _llm_tool_client = MagicMock(spec=openai_spec)

    global _llm_vision_client
    _llm_vision_client = MagicMock(spec=openai_spec)

    global _celery_inspect_service
    _celery_inspect_service = MagicMock(spec=CeleryInspectService)

    global _wipe_service
    _wipe_service = MagicMock(spec=WipeService)


def get_libretranslate_api() -> LibreTranslateAPI:
    if _libretranslate_api is None:
        raise DependencyException("Libretranslate api missing")
    return _libretranslate_api


def get_query_builder() -> QueryBuilder:
    if _query_builder is None:
        raise DependencyException("QueryBuilder missing")
    return _query_builder


def get_redis_client() -> StrictRedis:
    if _redis_client is None:
        raise DependencyException("Redis client is missing")
    return _redis_client


def get_redis_client_async() -> StrictRedisAsync:
    if _redis_client_async is None:
        raise DependencyException("Async Redis client is missing")
    return _redis_client_async


def get_redis_cache_client() -> StrictRedis:
    if _redis_cache_client is None:
        raise DependencyException("Redis cache client is missing")
    return _redis_cache_client


def get_pubsub_service() -> PubSubService:
    if _pubsub_service is None:
        raise DependencyException("Pubsub service is missing")
    return _pubsub_service


def get_elasticsearch() -> Elasticsearch:
    if _elasticsearch is None:
        raise DependencyException("Elasticsearch not initialized")
    return _elasticsearch


def get_file_storage_service() -> FileStorageLazyBytesService:
    if _file_storage_service is None:
        raise DependencyException("File Storage Service missing")
    return _file_storage_service


def get_root_task_information_repository() -> RootTaskInformationRepository:
    if _root_task_information_repository is None:
        raise DependencyException("Root task information repository not loaded")
    return _root_task_information_repository


def get_lazybytes_service() -> TempLazyBytesService:
    if _lazybytes_service is None:
        raise DependencyException("Lazybytes Service missing")
    return _lazybytes_service


def get_imap_service() -> IMAPService:
    if _imap_service is None:
        raise DependencyException("IMAP Service missing")
    return _imap_service


def get_s3_intake_client() -> Minio:
    if _s3_intake_client is None:
        raise DependencyException("S3 intake client missing")
    return _s3_intake_client


def get_celery_app() -> "Celery[BaseTask]":
    if _celery_app is None:
        raise DependencyException("Celery app not initialized")
    return _celery_app


def get_queues_service() -> QueuesService:
    if _queues_service is None:
        raise DependencyException("Queues service is missing")
    return _queues_service


def get_archive_repository() -> ArchiveRepository:
    if _archive_repository is None:
        raise DependencyException("Archive Repository missing")
    return _archive_repository


def get_file_repository() -> FileRepository:
    if _file_repository is None:
        raise DependencyException("File Repository missing")
    return _file_repository


def get_ai_context_repository() -> AiContextRepository:
    if _ai_context_repository is None:
        raise DependencyException("AiContext Repository missing")
    return _ai_context_repository


def get_task_scheduling_service() -> TaskSchedulingService:
    if _task_scheduling_service is None:
        raise DependencyException("Task Scheduling Service missing")
    return _task_scheduling_service


def get_file_scheduling_service() -> FileSchedulingService:
    if _file_scheduling_service is None:
        raise DependencyException("File Scheduling Service missing")
    return _file_scheduling_service


def get_archive_scheduling_service() -> ArchiveSchedulingService:
    if _archive_scheduling_service is None:
        raise DependencyException("Archive Scheduling Service missing")
    return _archive_scheduling_service


def get_ai_scheduling_service() -> AiSchedulingService:
    if _ai_scheduling_service is None:
        raise DependencyException("Ai Scheduling Service missing")
    return _ai_scheduling_service


def get_archive_encryption_service() -> ArchiveEncryptionService:
    if _archive_encryption_service is None:
        raise DependencyException("Archive Encryption Service missing")
    return _archive_encryption_service


def get_llm_summarization_client() -> OpenAI:
    if _llm_summarization_client is None:
        raise DependencyException("LLM summarization client missing")
    return _llm_summarization_client


def get_llm_hyde_client() -> OpenAI:
    if _llm_hyde_client is None:
        raise DependencyException("LLM hyde client missing")
    return _llm_hyde_client


def get_llm_rerank_client() -> OpenAI:
    if _llm_rerank_client is None:
        raise DependencyException("LLM rerank client missing")
    return _llm_rerank_client


def get_llm_chat_client() -> OpenAI:
    if _llm_chat_client is None:
        raise DependencyException("LLM chat client missing")
    return _llm_chat_client


def get_llm_embedding_client() -> OpenAI:
    if _llm_embedding_client is None:
        raise DependencyException("LLM embedding client missing")
    return _llm_embedding_client


def get_llm_tool_client() -> OpenAI:
    if _llm_tool_client is None:
        raise DependencyException("LLM tool client missing")
    return _llm_tool_client


def get_llm_vision_client() -> OpenAI:
    if _llm_vision_client is None:
        raise DependencyException("LLM vision client missing")
    return _llm_vision_client


def get_celery_inspect_service() -> CeleryInspectService:
    if _celery_inspect_service is None:
        raise DependencyException("CeleryInspect Service missing")
    return _celery_inspect_service


def get_wipe_service() -> WipeService:
    if _wipe_service is None:
        raise DependencyException("Wipe service missing")
    return _wipe_service
