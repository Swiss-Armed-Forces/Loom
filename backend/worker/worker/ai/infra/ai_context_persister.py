from common.ai_context.ai_context_repository import AiContext, AiContextRepository
from common.dependencies import get_ai_context_repository

from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _set_state(obj: AiContext, state: str) -> None:
    obj.state = state


class AiContextPersister(PersisterBase[AiContext]):
    @classmethod
    def get_repository(cls) -> AiContextRepository:
        repository = get_ai_context_repository()
        return repository

    # Bind mutations as class attributes
    set_state = mutation(_set_state)
