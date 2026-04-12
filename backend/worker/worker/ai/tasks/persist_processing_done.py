from typing import Any
from uuid import UUID

from celery import chain
from celery.canvas import Signature
from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_persister import AiContextPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(context_id: UUID) -> Signature:
    return chain(
        persist_processing_done_task.s(context_id),
    )


@persisting_task(app, AiContextPersister)
def persist_processing_done_task(persister: AiContextPersister, _: Any):
    persister.set_state("processed")
