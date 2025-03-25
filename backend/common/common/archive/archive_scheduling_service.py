""" "ArchiveSchedulingService handles the creation of new archives."""

from common.archive.archive_repository import Archive, ArchiveRepository
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService


class ArchiveSchedulingService:
    """Handles the creation of new archives."""

    def __init__(
        self,
        archive_repository: ArchiveRepository,
        task_scheduling_service: TaskSchedulingService,
    ):
        self._archive_repository = archive_repository
        self._task_scheduling_service = task_scheduling_service

    def create_archive(self, query: QueryParameters) -> Archive:
        """Create an archive that will contain all files that match the query."""
        archive = Archive(
            query=query,
        )

        self._archive_repository.save(archive)
        self._task_scheduling_service.create_archive(archive)

        return archive
