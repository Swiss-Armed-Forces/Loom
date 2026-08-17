from common.ai_context.ai_context_repository import AiQuestion
from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_persister import AiContextPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, AiContextPersister)
def persist_question_task(persister: AiContextPersister, question: AiQuestion) -> None:
    persister.append_question(question)
