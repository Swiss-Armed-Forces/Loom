from celery.utils.log import get_task_logger
from common.dependencies import get_file_repository
from common.file.file_repository import File
from common.models.base_repository import BaseRepository

from worker.utils.processing_task import ProcessingTask

logger = get_task_logger(__name__)


class FileIndexingTask(ProcessingTask[File, File]):
    """A base task for all file indexing tasks.

    It keeps track of the status of task and subtask
    """

    # pylint does not consider metaclass:
    # https://stackoverflow.com/questions/22186843/pylint-w0223-method-is-abstract-in-class-but-is-not-overridden
    # pylint: disable=abstract-method

    @property
    def _repository(self) -> BaseRepository[File]:
        repository = get_file_repository()
        return repository
