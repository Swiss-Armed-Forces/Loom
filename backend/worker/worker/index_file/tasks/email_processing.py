import logging

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.processor.email_processor import (
    detect_spam,
    is_email,
    upload_email_to_imap,
)
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(file_content: LazyBytes, file: File) -> Signature:
    return chain(
        detect_email_task.s(file.extension),
        group(
            chain(detect_spam_task.s(file_content), persist_spam_task.s(file)),
            upload_email_to_imap_task.s(file_content, file),
        ),
    )


@app.task(base=FileIndexingTask)
def detect_email_task(
    tika_file_type: str,
    file_extension: str,
) -> bool:
    return is_email(extension=file_extension, mimetype=tika_file_type)


@app.task(base=FileIndexingTask)
def detect_spam_task(
    is_email_detected: bool,
    file_content: LazyBytes,
) -> bool:
    if not is_email_detected:
        return False

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        return detect_spam(memview)


@persisting_task(app, IndexingPersister)
def persist_spam_task(persister: IndexingPersister, is_spam: bool):
    """Persists the spam decision."""
    persister.set_is_spam(is_spam)


@app.task(base=FileIndexingTask)
def upload_email_to_imap_task(
    is_email_detected: bool,
    file_content: LazyBytes,
    file: File,
):
    if not is_email_detected:
        return

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        upload_email_to_imap(file.full_path, memview)
