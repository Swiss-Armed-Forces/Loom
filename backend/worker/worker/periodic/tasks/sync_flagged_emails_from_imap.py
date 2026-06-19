import logging
from uuid import UUID

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
    get_imap_service,
    get_lazybytes_service,
)
from common.file.file_repository import ImapInfo
from common.services.lazybytes_service import TempTypedLazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return fetch_flagged_emails_from_imap.s()


@app.task(base=PeriodicTask)
def fetch_flagged_emails_from_imap():
    flagged_in_imap = get_imap_service().get_emails(["FLAGGED"], recurse=True)
    lazybytes_service = get_lazybytes_service()

    for imap_info in flagged_in_imap:
        chain(
            get_id_from_imap_info_task.s(lazybytes_service.from_object(imap_info)),
            process_email_to_flag.s(),
            set_flag_for_file.s(True),
        ).delay().forget()


@app.task(base=PeriodicTask)
def get_id_from_imap_info_task(imap_info_lb: TempTypedLazyBytes[ImapInfo]) -> UUID:
    imap_info = get_lazybytes_service().load_object(imap_info_lb)

    file_repository = get_file_repository()
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
    )
    file = file_repository.get_email_from_imap_info(query, imap_info)
    return file.id_


@app.task(base=PeriodicTask)
def process_email_to_flag(
    file_id: UUID,
) -> UUID | None:
    file = get_file_repository().get_by_id(file_id)

    if file is None:
        raise ValueError(f"File with id {file_id} not found")

    if file.flagged:
        return None

    return file_id


@app.task(base=PeriodicTask)
def set_flag_for_file(file_id: UUID | None, flag_state: bool):
    if file_id is None:
        return

    get_file_scheduling_service().update_file(
        file_id, UpdateFileRequest(flagged=flag_state)
    )
