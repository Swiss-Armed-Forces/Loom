import logging
from uuid import UUID

from common.dependencies import get_celery_app, get_file_repository, get_imap_service

from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()

IMAP_FLAGGED_FLAG = b"\\Flagged"


@app.task(base=FileIndexingTask)
def sync_flag_to_imap(file_id: UUID, flag_state: bool):
    file = get_file_repository().get_by_id(file_id)

    if file is None:
        logger.warning("File with id %s not found, skipping IMAP flag sync", file_id)
        return

    if file.imap is None:
        return

    imap_service = get_imap_service()
    if flag_state:
        imap_service.add_flags_to_emails(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG],
        )
    else:
        imap_service.remove_flags_from_emails(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG],
        )
