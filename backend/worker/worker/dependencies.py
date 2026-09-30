import logging
from types import NoneType
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import (
    DependencyException,
    get_celery_app,
    get_celery_inspect_service,
    get_lazybytes_service,
)
from common.llm.agent import build_agent
from common.llm.embedder import build_embedder
from common.llm.return_types import (
    DetectedLanguage,
    ElasticsearchQuery,
    ImageDescriptionResult,
    SummarizationResult,
    TranslationResult,
)
from common.models.base_repository import REPOSITORY_INSTANCES, BaseRepository
from gotenberg_client import GotenbergClient
from pydantic_ai import Agent, Embedder

from worker.services.rspamd_service import RspamdService
from worker.services.seaweedfs_shell_service import SeaweedFSShellService
from worker.services.tika_service import TikaService
from worker.settings import settings
from worker.utils.task_info_persister import TaskInfoPersister

# Note, "= None" assignments are needed here to make flake8 happy
_tika_service: TikaService | None = None
_rspamd_service: RspamdService | None = None
_gotenberg_client: GotenbergClient | None = None
_seaweedfs_shell_service: SeaweedFSShellService | None = None

# Task info persisters - cached per repository type to avoid creating new classes per call
_task_info_persisters: dict[type[BaseRepository], type[TaskInfoPersister]] = {}
_tasks_registered: bool = False

# Agents
_llm_hyde_agent: Agent[None, str] | None = None
_llm_rag_rerank_agent: Agent[None, float] | None = None
_llm_rag_synthesize_agent: Agent[None, str] | None = None
_llm_vision_agent: Agent[None, ImageDescriptionResult] | None = None
_llm_suggest_queries_agent: Agent[None, ElasticsearchQuery] | None = None
_llm_translation_agent: Agent[None, TranslationResult] | None = None
_llm_language_detection_agent: Agent[None, list[DetectedLanguage]] | None = None
_llm_summarization_key_points_agent: Agent[None, SummarizationResult] | None = None
_llm_summarization_agent: Agent[None, SummarizationResult] | None = None
_llm_summarization_refine_agent: Agent[None, SummarizationResult] | None = None
_llm_embedder: Embedder | None = None

logger = logging.getLogger(__name__)


def _register_task_info_persister(repo_type: type[BaseRepository]) -> None:
    """Create and cache a TaskInfoPersister class for a repository type."""

    class BoundTaskInfoPersister(TaskInfoPersister):
        @classmethod
        def get_repository(cls):
            return REPOSITORY_INSTANCES[repo_type]

    _task_info_persisters[repo_type] = BoundTaskInfoPersister


def init():
    # pylint: disable=global-statement
    common_dependencies.init()
    logger.info("Initialize worker dependencies")

    global _tasks_registered
    if not _tasks_registered:
        app = get_celery_app()
        register_tasks_for_package(app=app, package="worker")  # type: ignore[arg-type]
        for repo_type in REPOSITORY_INSTANCES:
            _register_task_info_persister(repo_type)
        _tasks_registered = True

    get_celery_inspect_service().register_task_groups()

    global _tika_service
    _tika_service = TikaService(
        get_lazybytes_service(),
        timeout=settings.tika_timeout_seconds,
    )

    global _rspamd_service
    _rspamd_service = RspamdService(settings.rspam_host)

    global _gotenberg_client
    _gotenberg_client = GotenbergClient(
        str(settings.gotenberg_host), timeout=settings.gotenberg_timeout_seconds
    )

    global _seaweedfs_shell_service
    _seaweedfs_shell_service = SeaweedFSShellService(
        master_host=settings.seaweedfs_master_host,
        timeout=settings.seaweedfs_shell_timeout,
    )

    # Agents
    global _llm_hyde_agent
    _llm_hyde_agent = build_agent(NoneType, str, settings.llm.rag_hyde)

    global _llm_rag_rerank_agent
    _llm_rag_rerank_agent = build_agent(NoneType, float, settings.llm.rag_rerank)

    global _llm_rag_synthesize_agent
    _llm_rag_synthesize_agent = build_agent(NoneType, str, settings.llm.rag_synthesize)

    global _llm_vision_agent
    _llm_vision_agent = build_agent(
        NoneType, ImageDescriptionResult, settings.llm.vision
    )

    global _llm_suggest_queries_agent
    _llm_suggest_queries_agent = build_agent(
        NoneType, ElasticsearchQuery, settings.llm.suggest_queries
    )

    global _llm_translation_agent
    _llm_translation_agent = build_agent(
        NoneType, TranslationResult, settings.llm.translation
    )

    global _llm_language_detection_agent
    _llm_language_detection_agent = build_agent(
        NoneType, list[DetectedLanguage], settings.llm.language_detection
    )

    global _llm_summarization_key_points_agent
    _llm_summarization_key_points_agent = build_agent(
        NoneType, SummarizationResult, settings.llm.summarization_key_points
    )

    global _llm_summarization_agent
    _llm_summarization_agent = build_agent(
        NoneType, SummarizationResult, settings.llm.summarization
    )

    global _llm_summarization_refine_agent
    _llm_summarization_refine_agent = build_agent(
        NoneType, SummarizationResult, settings.llm.summarization_refine
    )

    global _llm_embedder
    _llm_embedder = build_embedder(settings.llm.embedding)


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()
    global _tika_service
    _tika_service = MagicMock(spec=TikaService)

    global _rspamd_service
    _rspamd_service = MagicMock(spec=RspamdService)

    global _gotenberg_client
    _gotenberg_client = MagicMock(spec=GotenbergClient)

    global _seaweedfs_shell_service
    _seaweedfs_shell_service = MagicMock(spec=SeaweedFSShellService)

    # Initialize repository instances with mocks for fresh test state
    for repo_type in REPOSITORY_INSTANCES:
        REPOSITORY_INSTANCES[repo_type] = MagicMock(spec=repo_type)

    # Agents
    global _llm_hyde_agent
    _llm_hyde_agent = MagicMock(spec=Agent[NoneType, str])

    global _llm_rag_rerank_agent
    _llm_rag_rerank_agent = MagicMock(spec=Agent[NoneType, float])

    global _llm_rag_synthesize_agent
    _llm_rag_synthesize_agent = MagicMock(spec=Agent[NoneType, str])

    global _llm_vision_agent
    _llm_vision_agent = MagicMock(spec=Agent[NoneType, ImageDescriptionResult])

    global _llm_suggest_queries_agent
    _llm_suggest_queries_agent = MagicMock(spec=Agent[NoneType, ElasticsearchQuery])

    global _llm_translation_agent
    _llm_translation_agent = MagicMock(spec=Agent[NoneType, TranslationResult])

    global _llm_language_detection_agent
    _llm_language_detection_agent = MagicMock(
        spec=Agent[NoneType, list[DetectedLanguage]]
    )

    global _llm_summarization_key_points_agent
    _llm_summarization_key_points_agent = MagicMock(
        spec=Agent[NoneType, SummarizationResult]
    )

    global _llm_summarization_agent
    _llm_summarization_agent = MagicMock(spec=Agent[NoneType, SummarizationResult])

    global _llm_summarization_refine_agent
    _llm_summarization_refine_agent = MagicMock(
        spec=Agent[NoneType, SummarizationResult]
    )

    global _llm_embedder
    _llm_embedder = MagicMock(spec=Embedder)


def get_tika_service() -> TikaService:
    if _tika_service is None:
        raise DependencyException("Tika Service missing")
    return _tika_service


def get_rspamd_service() -> RspamdService:
    if _rspamd_service is None:
        raise DependencyException("Rspamd Service missing")
    return _rspamd_service


def get_gotenberg_client() -> GotenbergClient:
    if _gotenberg_client is None:
        raise DependencyException("Gotenberg Client missing")
    return _gotenberg_client


def get_seaweedfs_shell_service() -> SeaweedFSShellService:
    if _seaweedfs_shell_service is None:
        raise DependencyException("SeaweedFS Shell Service missing")
    return _seaweedfs_shell_service


def get_task_info_persister(
    repository_type: type[BaseRepository],
) -> type[TaskInfoPersister]:
    """Get the task info persister class for a repository type."""
    if repository_type not in _task_info_persisters:
        raise DependencyException(f"No task info persister for {repository_type}")
    return _task_info_persisters[repository_type]


def get_llm_hyde_agent() -> Agent[None, str]:
    if _llm_hyde_agent is None:
        raise DependencyException("LLM hyde agent missing")
    return _llm_hyde_agent


def get_llm_rag_rerank_agent() -> Agent[None, float]:
    if _llm_rag_rerank_agent is None:
        raise DependencyException("LLM rerank agent missing")
    return _llm_rag_rerank_agent


def get_llm_rag_synthesize_agent() -> Agent[None, str]:
    if _llm_rag_synthesize_agent is None:
        raise DependencyException("LLM rag synthesize agent missing")
    return _llm_rag_synthesize_agent


def get_llm_vision_agent() -> Agent[None, ImageDescriptionResult]:
    if _llm_vision_agent is None:
        raise DependencyException("LLM vision agent missing")
    return _llm_vision_agent


def get_llm_suggest_queries_agent() -> Agent[None, ElasticsearchQuery]:
    if _llm_suggest_queries_agent is None:
        raise DependencyException("LLM suggest queries agent missing")
    return _llm_suggest_queries_agent


def get_llm_translation_agent() -> Agent[None, TranslationResult]:
    if _llm_translation_agent is None:
        raise DependencyException("LLM translation agent missing")
    return _llm_translation_agent


def get_llm_language_detection_agent() -> Agent[None, list[DetectedLanguage]]:
    if _llm_language_detection_agent is None:
        raise DependencyException("LLM language detection agent missing")
    return _llm_language_detection_agent


def get_llm_summarization_key_points_agent() -> Agent[None, SummarizationResult]:
    if _llm_summarization_key_points_agent is None:
        raise DependencyException("LLM summarization key points agent missing")
    return _llm_summarization_key_points_agent


def get_llm_summarization_agent() -> Agent[None, SummarizationResult]:
    if _llm_summarization_agent is None:
        raise DependencyException("LLM summarization agent missing")
    return _llm_summarization_agent


def get_llm_summarization_refine_agent() -> Agent[None, SummarizationResult]:
    if _llm_summarization_refine_agent is None:
        raise DependencyException("LLM summarization refine agent missing")
    return _llm_summarization_refine_agent


def get_llm_embedder() -> Embedder:
    if _llm_embedder is None:
        raise DependencyException("LLM embedder missing")
    return _llm_embedder
