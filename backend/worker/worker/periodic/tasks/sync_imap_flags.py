import logging
from uuid import UUID

from celery import chain, chord
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
    get_imap_service,
    get_lazybytes_service,
)
from common.file.file_repository import FileNotFoundException, ImapInfo
from common.services.lazybytes_service import TempTypedLazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return chord(
        [fetch_flagged_emails_task.s(), fetch_seen_emails_task.s()],
        sync_imap_flags_task.s(),
    )


@app.task(base=PeriodicTask)
def fetch_flagged_emails_task() -> TempTypedLazyBytes[set[ImapInfo]]:
    flagged = set(get_imap_service().get_emails(["FLAGGED"], recurse=True))
    return get_lazybytes_service().from_object(flagged)


@app.task(base=PeriodicTask)
def fetch_seen_emails_task() -> TempTypedLazyBytes[set[ImapInfo]]:
    seen = set(get_imap_service().get_emails(["SEEN"], recurse=True))
    return get_lazybytes_service().from_object(seen)


@app.task(base=PeriodicTask)
def sync_imap_flags_task(
    fetch_results: list[TempTypedLazyBytes[set[ImapInfo]]],
):
    flagged_lb, seen_lb = fetch_results
    lazybytes_service = get_lazybytes_service()
    flagged_in_imap: set[ImapInfo] = lazybytes_service.load_object(flagged_lb)
    seen_in_imap: set[ImapInfo] = lazybytes_service.load_object(seen_lb)

    for imap_info in flagged_in_imap | seen_in_imap:
        flagged = imap_info in flagged_in_imap
        seen = imap_info in seen_in_imap
        chain(
            get_id_from_imap_info_task.s(lazybytes_service.from_object(imap_info)),
            set_flags_for_file_task.s(flagged, seen),
        ).delay().forget()


@app.task(base=PeriodicTask)
def get_id_from_imap_info_task(
    imap_info_lb: TempTypedLazyBytes[ImapInfo],
) -> UUID | None:
    imap_info = get_lazybytes_service().load_object(imap_info_lb)

    file_repository = get_file_repository()
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
    )
    try:
        file = file_repository.get_email_from_imap_info(query, imap_info)
    except FileNotFoundException:
        logger.warning(
            "No Loom file found for IMAP email folder=%s uid=%s, skipping flag sync",
            imap_info.folder,
            imap_info.uid,
        )
        return None

    return file.id_


@app.task(base=PeriodicTask)
def set_flags_for_file_task(file_id: UUID | None, flagged: bool, seen: bool):
    if file_id is None:
        return

    get_file_scheduling_service().update_file(
        file_id,
        UpdateFileRequest(flagged=flagged, seen=seen),
    )
