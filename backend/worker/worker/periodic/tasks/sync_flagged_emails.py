import logging
from uuid import UUID

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
    get_imap_service,
    get_lazybytes_service,
)
from common.file.file_repository import File, ImapInfo
from common.services.lazybytes_service import TypedLazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest
from pydantic import BaseModel

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


class FlaggedEmailsChanges(BaseModel):
    # emails that are flagged in imap and not in loom, we only have the ImapInfo
    emails_to_flag: list[ImapInfo]
    # emails that are flagged in loom but not in imap
    emails_to_unflag: list[UUID]


def signature() -> Signature:
    return group(fetch_flagged_emails_from_imap.s(), fetch_flagged_emails_from_loom.s())


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
def get_id_from_imap_info_task(imap_info_lb: TypedLazyBytes[ImapInfo]) -> UUID:
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
def fetch_flagged_emails_from_loom():
    lazybytes_service = get_lazybytes_service()
    file_repository = get_file_repository()

    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
        search_string="flagged:true",
    )
    for file in file_repository.get_emails(query):
        chain(
            process_email_to_unflag.s(lazybytes_service.from_object(file)),
            set_flag_for_file.s(False),
        ).delay().forget()


@app.task(base=PeriodicTask)
def process_email_to_unflag(file_lb: TypedLazyBytes[File]) -> UUID | None:
    file = get_lazybytes_service().load_object(file_lb)

    if file.imap is None or b"\\Flagged" in get_imap_service().get_flags_from_imap_info(
        file.imap
    ):
        return None
    return file.id_


@app.task(base=PeriodicTask)
def set_flag_for_file(file_id: UUID | None, flag_state: bool):
    if file_id is None:
        return

    get_file_scheduling_service().update_file(
        file_id, UpdateFileRequest(flagged=flag_state)
    )
