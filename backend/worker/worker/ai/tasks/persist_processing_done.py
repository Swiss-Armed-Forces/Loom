from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_persister import AiContextPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, AiContextPersister)
def persist_processing_done_task(persister: AiContextPersister) -> None:
    persister.set_state("processed")
