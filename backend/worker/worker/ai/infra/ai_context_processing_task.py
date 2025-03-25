from common.ai_context.ai_context_repository import AiContext
from common.dependencies import get_ai_context_repository
from common.models.base_repository import BaseRepository

from worker.utils.processing_task import ProcessingTask


class AiContextProcessingTask(ProcessingTask[AiContext, AiContext]):
    # pylint does not consider metaclass:
    # https://stackoverflow.com/questions/22186843/pylint-w0223-method-is-abstract-in-class-but-is-not-overridden
    # pylint: disable=abstract-method

    @property
    def _repository(self) -> BaseRepository[AiContext]:
        repository = get_ai_context_repository()
        return repository
