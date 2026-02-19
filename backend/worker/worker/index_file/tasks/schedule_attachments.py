import logging
from hashlib import sha256

from celery import chain, group
from common.dependencies import (
    get_celery_app,
    get_file_scheduling_service,
    get_lazybytes_service,
)
from common.file.file_repository import Attachment, File

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TikaAttachment, TikaResult
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(bind=True, base=FileIndexingTask)
def schedule_attachments(self: FileIndexingTask, tika_result: TikaResult, file: File):
    """Schedule tasks to dispatch the attachment processing of an file.

    Note: that tika processes archives (i.e. zip, tar, etc.) as attachments, so this
    also handles these types of files through the tika processing.
    """
    return self.replace(
        group(
            *[
                chain(
                    schedule_attachment.s(attachment, file), persist_attachment.s(file)
                )
                for attachment in tika_result.attachments
            ]
        )
    )


@app.task(base=FileIndexingTask)
def schedule_attachment(
    tika_attachment: TikaAttachment, file: File
) -> Attachment | None:
    file_data_hash = sha256()
    with get_lazybytes_service().load_generator(
        tika_attachment.data
    ) as file_chunk_generator:
        for file_chunk in file_chunk_generator:
            file_data_hash.update(file_chunk)

    attachment_name = str(file.full_name / tika_attachment.name)
    if file.sha256 == file_data_hash.hexdigest():
        # avoid scheduling same file again: will lead to endless indexing loops
        logger.info(
            "Attachment ('%s') has same sha256 hash as parent ('%s'): skipping",
            attachment_name,
            file.full_name,
        )
        return None

    new_file = get_file_scheduling_service().index_file(
        full_name=attachment_name,
        file_content=tika_attachment.data,
        source_id=file.source,
        parent_id=file.id_,
    )
    return Attachment(
        id=new_file.id_,
        name=tika_attachment.name,
    )


@persisting_task(
    app,
    IndexingPersister,
)
def persist_attachment(persister: IndexingPersister, attachment: Attachment | None):
    if attachment is None:
        return
    persister.add_or_replace_attachment(attachment)
