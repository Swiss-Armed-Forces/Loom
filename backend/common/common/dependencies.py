import logging
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

from celery import Celery
from elasticsearch import Elasticsearch
from libretranslatepy import LibreTranslateAPI
from ollama import Client
from pymongo import MongoClient
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
from common.services.file_storage_service import FileStorageService
from common.services.lazybytes_service import GridFSLazyBytesService, LazyBytesService
from common.services.query_builder import QueryBuilder
from common.services.queues_service import QueuesService
from common.services.task_scheduling_service import TaskSchedulingService
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
_elasticsearch: Elasticsearch | None = None
_mongo: MongoClient | None = None
_celery_app: Optional["Celery[BaseTask]"] = None
_redis_client: StrictRedis | None = None
_redis_client_async: StrictRedisAsync | None = None
_pubsub_service: PubSubService | None = None
_queues_service: QueuesService | None = None
_file_storage_service: FileStorageService | None = None
_archive_repository: ArchiveRepository | None = None
_file_repository: FileRepository | None = None
_ai_context_repository: AiContextRepository | None = None
_root_task_information_repository: RootTaskInformationRepository | None = None
_file_scheduling_service: FileSchedulingService | None = None
_task_scheduling_service: TaskSchedulingService | None = None
_archive_scheduling_service: ArchiveSchedulingService | None = None
_ai_scheduling_service: AiSchedulingService | None = None
_archive_encryption_service: ArchiveEncryptionService | None = None
_lazybytes_service: LazyBytesService | None = None
_ollama_client: Client | None = None
_ollama_tool_client: Client | None = None


logger = logging.getLogger(__name__)


def init(init_elasticsearch_documents: bool = False):
    # pylint: disable=global-statement
    logger.info("Initializes common dependencies")

    global _libretranslate_api
    _libretranslate_api = LibreTranslateAPI(str(settings.translate_host))

    global _query_builder
    _query_builder = QueryBuilder(_libretranslate_api)

    global _redis_client
    _redis_client = StrictRedis.from_url(str(settings.celery_backend_host))

    global _redis_client_async
    _redis_client_async = StrictRedisAsync.from_url(str(settings.celery_backend_host))

    global _pubsub_service
    _pubsub_service = PubSubService(_redis_client, _redis_client_async)

    global _elasticsearch
    _elasticsearch = init_elasticsearch(
        _query_builder, _pubsub_service, init_elasticsearch_documents
    )

    global _mongo
    # pymongo uuid representation:
    # https://pymongo.readthedocs.io/en/stable/examples/uuid.html
    _mongo = MongoClient(
        str(settings.mongo_db_host),
        uuidRepresentation="standard",
    )

    global _celery_app
    _celery_app = init_celery_app()

    global _queues_service
    _queues_service = QueuesService(str(settings.rabbit_mq_management_host))

    global _file_storage_service
    _file_storage_service = FileStorageService(
        _mongo.get_database(settings.mongo_db_file_storage_name)
    )

    global _archive_repository
    _archive_repository = ArchiveRepository(_query_builder, _pubsub_service)

    global _file_repository
    _file_repository = FileRepository(_query_builder, _pubsub_service)

    global _ai_context_repository
    _ai_context_repository = AiContextRepository(_query_builder, _pubsub_service)

    global _root_task_information_repository
    _root_task_information_repository = RootTaskInformationRepository(
        _mongo.get_database(settings.mongo_db_repositories_storage_name)
    )

    global _lazybytes_service
    _lazybytes_service = GridFSLazyBytesService(
        _mongo.get_database(settings.mongo_db_lazybytes_storage_name)
    )

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
        settings.archive_encryption_master_key
    )

    global _ollama_client
    _ollama_client = Client(str(settings.ollama_host), timeout=settings.ollama_timeout)

    global _ollama_tool_client
    _ollama_tool_client = Client(
        str(settings.ollama_tool_host), timeout=settings.ollama_timeout
    )


# pylint: disable=too-many-statements
def mock_init():
    # pylint: disable=global-statement
    logger.info("Initializes global mock dependencies")

    global _libretranslate_api
    _libretranslate_api = MagicMock(spec=LibreTranslateAPI)

    global _query_builder
    _query_builder = MagicMock(spec=QueryBuilder)

    global _elasticsearch
    _elasticsearch = MagicMock(spec=Elasticsearch)

    global _mongo
    _mongo = MagicMock(spec=MongoClient)

    global _celery_app
    _celery_app = MagicMock(spec=Celery)
    # make the task decorator work: needed if we want to tests tasks
    _celery_app.task = noop_decorator

    global _queues_service
    _queues_service = MagicMock(spec=QueuesService)

    global _pubsub_service
    _pubsub_service = MagicMock(spec=PubSubService)

    global _redis_client
    _redis_client = MagicMock(spec=StrictRedis)

    global _redis_client_async
    _redis_client_async = AsyncMock(spec=StrictRedisAsync)

    global _file_storage_service
    _file_storage_service = MagicMock(spec=FileStorageService)

    global _archive_repository
    _archive_repository = MagicMock(spec=ArchiveRepository)

    global _file_repository
    _file_repository = MagicMock(spec=FileRepository)

    global _ai_context_repository
    _ai_context_repository = MagicMock(spec=AiContextRepository)

    global _root_task_information_repository
    _root_task_information_repository = MagicMock(spec=RootTaskInformationRepository)

    global _lazybytes_service
    _lazybytes_service = MagicMock(spec=LazyBytesService)

    global _file_scheduling_service
    _file_scheduling_service = MagicMock(spec=FileSchedulingService)

    global _task_scheduling_service
    _task_scheduling_service = MagicMock(spec=TaskSchedulingService)

    global _archive_scheduling_service
    _archive_scheduling_service = MagicMock(spec=ArchiveSchedulingService)

    global _ai_scheduling_service
    _ai_scheduling_service = MagicMock(spec=AiSchedulingService)

    global _archive_encryption_service
    _archive_encryption_service = MagicMock(spec=ArchiveEncryptionService)

    global _ollama_client
    _ollama_client = MagicMock(spec=Client)

    global _ollama_tool_client
    _ollama_tool_client = MagicMock(spec=Client)


def get_libretranslate_api() -> LibreTranslateAPI:
    if _libretranslate_api is None:
        raise DependencyException("Libretranslate api missing")
    return _libretranslate_api


def get_query_builder() -> QueryBuilder:
    if _query_builder is None:
        raise DependencyException("QueryBuilder missing")
    return _query_builder


def get_elasticsearch() -> Elasticsearch:
    if _elasticsearch is None:
        raise DependencyException("Elasticsearch not initialized")
    return _elasticsearch


def get_celery_app() -> "Celery[BaseTask]":
    if _celery_app is None:
        raise DependencyException("Celery app not initialized")
    return _celery_app


def get_queues_service() -> QueuesService:
    if _queues_service is None:
        raise DependencyException("Queues service is missing")
    return _queues_service


def get_redis_client() -> StrictRedis:
    if _redis_client is None:
        raise DependencyException("Redis client is missing")
    return _redis_client


def get_redis_client_async() -> StrictRedisAsync:
    if _redis_client_async is None:
        raise DependencyException("Async Redis client is missing")
    return _redis_client_async


def get_pubsub_service() -> PubSubService:
    if _pubsub_service is None:
        raise DependencyException("Pubsub service is missing")
    return _pubsub_service


def get_file_storage_service() -> FileStorageService:
    if _file_storage_service is None:
        raise DependencyException("File Storage Service missing")
    return _file_storage_service


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


def get_root_task_information_repository() -> RootTaskInformationRepository:
    if _root_task_information_repository is None:
        raise DependencyException("Root task information repository not loaded")
    return _root_task_information_repository


def get_file_scheduling_service() -> FileSchedulingService:
    if _file_scheduling_service is None:
        raise DependencyException("File Scheduling Service missing")
    return _file_scheduling_service


def get_task_scheduling_service() -> TaskSchedulingService:
    if _task_scheduling_service is None:
        raise DependencyException("Task Scheduling Service missing")
    return _task_scheduling_service


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


def get_lazybytes_service() -> LazyBytesService:
    if _lazybytes_service is None:
        raise DependencyException("Lazybytes Service missing")
    return _lazybytes_service


def get_ollama_client() -> Client:
    if _ollama_client is None:
        raise DependencyException("Ollama Client missing")
    return _ollama_client


def get_ollama_tool_client() -> Client:
    if _ollama_tool_client is None:
        raise DependencyException("Ollama Tool Client missing")
    return _ollama_tool_client
