import logging
from hashlib import sha256

from common.dependencies import (
    get_celery_app,
    get_file_scheduling_service,
    get_lazybytes_service,
)
from common.file.file_repository import File

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.services.tika_service import TikaAttachment, TikaResult

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def schedule_attachments(tika_result: TikaResult, file: File):
    """Schedule tasks to dispatch the attachment processing of an file.

    Note: that tika proccesses archives (i.e. zip, tar, ect.) as attachments, so this
    also handles these types of files through the tika processing.
    """
    for attachment in tika_result.attachments:
        # Note: we schedule here each tasks seperatly
        # and not in a group([..]): This is to avoid
        # that we are beeing OOM-Killed for files
        # with many attachments
        schedule_attachment.s(attachment, file).delay().forget()


@app.task(base=FileIndexingTask)
def schedule_attachment(attachment: TikaAttachment, file: File):
    file_data_hash = sha256()
    with get_lazybytes_service().load_generator(
        attachment.data
    ) as file_chunk_generator:
        for file_chunk in file_chunk_generator:
            file_data_hash.update(file_chunk)

    attachment_name = str(file.full_name / attachment.name)
    if file.sha256 == file_data_hash.hexdigest():
        logger.info(
            "Attachment ('%s') has same sha256 hash as parent ('%s'): skipping",
            attachment_name,
            file.full_name,
        )
        return

    get_file_scheduling_service().index_file(
        attachment_name,
        attachment.data,
        file.source,
        exclude_from_archives=True,
    )
