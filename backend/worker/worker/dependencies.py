import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import DependencyException, get_celery_app
from common.models.base_repository import REPOSITORY_INSTANCES, BaseRepository
from gotenberg_client import GotenbergClient

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

logger = logging.getLogger(__name__)


def _register_task_info_persister(repo_type: type[BaseRepository]) -> None:
    """Create and cache a TaskInfoPersister class for a repository type."""

    class BoundTaskInfoPersister(TaskInfoPersister):
        @classmethod
        def get_repository(cls):
            return REPOSITORY_INSTANCES[repo_type]

    _task_info_persisters[repo_type] = BoundTaskInfoPersister


def init(subprocess_reinit: bool = False):
    # pylint: disable=global-statement
    logger.info(
        "Initializes worker dependencies (subprocess_reinit=%s)", subprocess_reinit
    )

    if not subprocess_reinit:
        # Only register tasks on first init (parent process)
        app = get_celery_app()
        register_tasks_for_package(app=app, package="worker")  # type: ignore[arg-type]

    # Always reinit HTTP clients (fork-unsafe)
    global _tika_service
    _tika_service = TikaService(common_dependencies.get_lazybytes_service())

    global _rspamd_service
    _rspamd_service = RspamdService(settings.rspam_host)

    global _gotenberg_client
    _gotenberg_client = GotenbergClient(
        str(settings.gotenberg_host), timeout=settings.gotenberg_timeout
    )

    global _seaweedfs_shell_service
    _seaweedfs_shell_service = SeaweedFSShellService(
        master_host=settings.seaweedfs_master_host,
        timeout=settings.seaweedfs_shell_timeout,
    )

    if not subprocess_reinit:
        # Task info persisters only need to be created once
        for repo_type in REPOSITORY_INSTANCES:
            _register_task_info_persister(repo_type)


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
