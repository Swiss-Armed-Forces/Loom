import logging
from hashlib import sha256

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import Attachment, File
from common.services.lazybytes_service import TempTypedLazyBytes
from common.settings import settings
from common.utils.iterhash import iterhash

from worker.index_file.index_file_task import dispatch_index_file
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TikaAttachment, TikaResult
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def schedule_attachments(lazy_tika_result: TempTypedLazyBytes[TikaResult], file: File):
    tika_result = get_lazybytes_service().load_object(lazy_tika_result)

    if (
        settings.max_recursion_depth is not None
        and file.recursion_depth >= settings.max_recursion_depth
    ):
        logger.info(
            "Skipping %d attachment(s) of '%s': max recursion depth %d reached"
            " (file depth: %d)",
            len(tika_result.attachments),
            file.full_name,
            settings.max_recursion_depth,
            file.recursion_depth,
        )
        return

    # We spawn each attachment sub-pipeline independently rather than using
    # self.replace(group(...)) because constructing a Celery group with many
    # attachments (e.g., large archives) causes memory blowup - the entire group
    # is built in memory before execution.
    #
    # Trade-off: Using delay().forget() loses proper pipeline integration with
    # the parent task. Exceptions won't propagate to the parent, and task tracking
    # becomes independent. The "correct" approach would be self.replace(group(...))
    # but it's not feasible for files with many attachments.
    for attachment in tika_result.attachments:
        schedule_attachment.s(attachment, file).delay().forget()


@app.task(base=FileIndexingTask)
def schedule_attachment(tika_attachment: TikaAttachment, file: File) -> None:
    attachment_name = str(file.full_name / tika_attachment.name)

    lazybytes_service = get_lazybytes_service()
    file_storage_service = get_file_storage_service()

    # Copy from lazybytes to file_storage while computing hash in a single pass
    data_hash = sha256()
    data = iterhash(data_hash, lazybytes_service.load_generator(tika_attachment.data))
    file_content = file_storage_service.from_generator(data)

    if file.sha256 == data_hash.hexdigest():
        # Avoid scheduling same file again: would lead to endless indexing loops
        # Delete the file_storage entry we just created
        file_storage_service.delete(file_content)
        logger.info(
            "Attachment ('%s') has same sha256 hash as parent ('%s'): skipping",
            attachment_name,
            file.full_name,
        )
        return

    chain(
        dispatch_index_file.s(
            attachment_name,
            file_content,
            file.source,
            file.id_,
            None,  # uploaded_datetime
            file.recursion_depth + 1,
        ),
        persist_attachment.s(file.id_),
    ).delay().forget()


@persisting_task(
    app,
    IndexingPersister,
)
def persist_attachment(persister: IndexingPersister, new_file: File | None):
    if new_file is None:
        return
    persister.add_or_replace_attachment(
        Attachment(id=new_file.id_, name=new_file.full_name.name)
    )
