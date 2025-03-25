from common.ai_context.ai_context_repository import AiContext, AiContextRepository
from common.dependencies import get_ai_context_repository

from worker.utils.persister_base import PersisterBase


class AiContextPersister(PersisterBase[AiContext]):
    @classmethod
    def get_repository(cls) -> AiContextRepository:
        repository = get_ai_context_repository()
        return repository

    def set_state(self, state: str):
        self._object.state = state
