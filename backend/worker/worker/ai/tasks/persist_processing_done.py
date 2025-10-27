from typing import Any

from celery import chain
from celery.canvas import Signature
from common.ai_context.ai_context_repository import AiContext
from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_persister import AiContextPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(context: AiContext) -> Signature:
    return chain(
        persist_processing_done_task.s(context),
    )


@persisting_task(app, AiContextPersister)
def persist_processing_done_task(persister: AiContextPersister, _: Any):
    persister.set_state("processed")
