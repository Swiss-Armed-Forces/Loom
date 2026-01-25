import logging

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File, ImapInfo
from common.services.lazybytes_service import LazyBytes

from worker.dependencies import get_imap_service, get_rspamd_service
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

# see /etc/mime.types
EMAIL_MIMETYPES = ["message/rfc822"]
EMAIL_EXTENSIONS = [
    ".eml",
]


def signature(file_content: LazyBytes, file: File) -> Signature:
    return chain(
        detect_email_task.s(file.extension),
        group(
            chain(detect_spam_task.s(file_content), persist_spam_task.s(file)),
            chain(
                upload_email_to_imap_task.s(file_content, file),
                persist_imap_info.s(file),
            ),
        ),
    )


def is_email(extension: str, mimetype: str) -> bool:
    return extension in EMAIL_EXTENSIONS or mimetype in EMAIL_MIMETYPES


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

    rspamd_service = get_rspamd_service()

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        is_spam = rspamd_service.detect_spam(memview)
        return is_spam


@persisting_task(app, IndexingPersister)
def persist_spam_task(persister: IndexingPersister, is_spam: bool):
    """Persists the spam decision."""
    persister.set_is_spam(is_spam)


@app.task(base=FileIndexingTask)
def upload_email_to_imap_task(
    is_email_detected: bool,
    file_content: LazyBytes,
    file: File,
) -> ImapInfo | None:

    if not is_email_detected:
        return None

    imap_service = get_imap_service()
    email_file = file.full_path
    email_folder = file.full_path.parent

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        email = bytes(memview)
        uid = imap_service.get_uid_of_email(email, email_folder)
        if uid:
            logger.info(
                "Not uploading, IMAP deduplication: %s",
                email_file,
            )
            return ImapInfo(
                uid=uid,
                folder=email_folder,
            )
        imap_info = imap_service.append_email(email, email_folder)
        return imap_info


@persisting_task(app, IndexingPersister)
def persist_imap_info(persister: IndexingPersister, imap_info: ImapInfo | None):
    if imap_info is None:
        return
    persister.set_imap_info(imap_info)
