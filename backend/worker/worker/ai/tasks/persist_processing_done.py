from typing import Any

from celery import chain
from celery.canvas import Signature
from common.ai_context.ai_context_repository import AiContext
from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_persister import AiContextPersister
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.utils.async_task_branch import (
    WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX,
    AsyncBranchesNotCompleted,
    raise_if_has_incomplete_async_branches,
)
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(context: AiContext) -> Signature:
    return chain(
        wait_for_async_branches_to_complete.s(),
        persist_processing_done_task.s(context),
    )


@app.task(
    bind=True,
    base=AiContextProcessingTask,
    autoretry_for=tuple([AsyncBranchesNotCompleted]),
    retry_backoff=True,
    max_retries=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    retry_backoff_max=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX,
)
def wait_for_async_branches_to_complete(self: AiContextProcessingTask, args: Any):
    raise_if_has_incomplete_async_branches(self)
    return args


@persisting_task(app, AiContextPersister)
def persist_processing_done_task(persister: AiContextPersister, _: Any):
    persister.set_state("processed")
