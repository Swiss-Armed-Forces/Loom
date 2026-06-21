import logging
from uuid import UUID

from common.dependencies import get_celery_app, get_file_repository, get_imap_service

from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()

IMAP_FLAGGED_FLAG = b"\\Flagged"
IMAP_SEEN_FLAG = b"\\Seen"


@app.task(base=FileIndexingTask)
def sync_imap_flags_task(
    file_id: UUID, flagged: bool | None = None, seen: bool | None = None
):
    file = get_file_repository().get_by_id(file_id)

    if file is None:
        logger.warning("File with id %s not found, skipping IMAP flag sync", file_id)
        return

    if file.imap is None:
        return

    flags_to_add = []
    flags_to_remove = []

    if flagged is True:
        flags_to_add.append(IMAP_FLAGGED_FLAG)
    elif flagged is False:
        flags_to_remove.append(IMAP_FLAGGED_FLAG)

    if seen is True:
        flags_to_add.append(IMAP_SEEN_FLAG)
    elif seen is False:
        flags_to_remove.append(IMAP_SEEN_FLAG)

    imap_service = get_imap_service()

    if flags_to_add:
        imap_service.add_flags_to_emails(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=flags_to_add,
        )
    if flags_to_remove:
        imap_service.remove_flags_from_emails(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=flags_to_remove,
        )
