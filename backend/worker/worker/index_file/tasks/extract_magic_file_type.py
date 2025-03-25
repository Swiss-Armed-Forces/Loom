import logging

import magic
from celery import chain
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(file_content: LazyBytes, file: File) -> Signature:
    """Create the signature for the tasks chain that determines the file type and
    persists it by using the file magic library."""
    return chain(get_file_type.s(file_content), persist_file_type.s(file))


@app.task(base=FileIndexingTask)
def get_file_type(file_content: LazyBytes) -> str:
    """Returns the file type."""
    with get_lazybytes_service().load_file(file_content) as tempfile:
        file_type = magic.from_descriptor(tempfile.fileno(), mime=True)
    return file_type


@persisting_task(app, IndexingPersister)
def persist_file_type(persister: IndexingPersister, file_type: str):
    """Persists the file type."""
    persister.set_magic_file_type(file_type)
