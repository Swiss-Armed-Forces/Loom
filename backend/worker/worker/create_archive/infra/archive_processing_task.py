from common.archive.archive_repository import Archive
from common.dependencies import get_archive_repository
from common.models.base_repository import BaseRepository

from worker.utils.processing_task import ProcessingTask


class ArchiveProcessingTask(ProcessingTask[Archive, Archive]):
    # pylint does not consider metaclass:
    # https://stackoverflow.com/questions/22186843/pylint-w0223-method-is-abstract-in-class-but-is-not-overridden
    # pylint: disable=abstract-method

    @property
    def _repository(self) -> BaseRepository[Archive]:
        repository = get_archive_repository()
        return repository
