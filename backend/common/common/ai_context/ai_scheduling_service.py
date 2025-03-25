import logging
from uuid import UUID

from common.ai_context.ai_context_repository import (
    AiContext,
    AiContextNotFoundException,
    AiContextRepository,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService

logger = logging.getLogger(__name__)


class AiSchedulingService:

    def __init__(
        self,
        ai_repository: AiContextRepository,
        task_scheduling_service: TaskSchedulingService,
    ):
        self._ai_repository = ai_repository
        self._task_scheduling_service = task_scheduling_service

    def create_context(self, query: QueryParameters) -> AiContext:
        ai_context = AiContext(
            query=query,
        )

        self._ai_repository.save(ai_context)

        return ai_context

    def process_ai_question(self, context_id: UUID, question: str):
        logger.info("Processing question '%s'", question)
        context = self._ai_repository.get_by_id(context_id)
        if context is None:
            raise AiContextNotFoundException("Invalid context")

        # update state
        context.state = "processing"
        self._ai_repository.update(context, include={"state"})

        self._task_scheduling_service.ai_process_question(
            context=context, question=question
        )
