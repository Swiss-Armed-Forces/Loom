from typing import Any
from uuid import UUID

from celery import chain
from celery.canvas import Signature
from common.dependencies import get_celery_app

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(file_id: UUID) -> Signature:
    """Create the signature for the task that persists the processing done status."""
    return chain(
        persist_processing_done_task.s(file_id),
    )


@persisting_task(app, IndexingPersister)
def persist_processing_done_task(persister: IndexingPersister, _: Any):
    """Task that persists the processing done status."""
    persister.set_state("processed")
