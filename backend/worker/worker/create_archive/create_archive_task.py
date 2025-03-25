from bson import ObjectId
from celery import chain, group
from common.archive.archive_repository import Archive
from common.dependencies import get_celery_app

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks import (
    calculate_checksum,
    calculate_size,
    persist_processing_done,
)
from worker.create_archive.tasks.compress_files import compress_files_task
from worker.create_archive.tasks.encrypt_file import encrypt_file_task
from worker.create_archive.tasks.link_files_with_archive import link_files_with_archive
from worker.create_archive.tasks.query_file_list import query_file_list_for_archive_task
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def create_archive_task(archive: Archive):
    chain(
        query_file_list_for_archive_task.s(archive.query),
        group(
            link_files_with_archive.s(archive.id_),
            chain(
                compress_files_task.s(),
                group(
                    persist_plain_file_storage_id_task.s(archive),
                    group(
                        calculate_checksum.signature_plain_file(archive),
                        calculate_size.signature_plain_file(archive),
                    ),
                    chain(
                        encrypt_file_task.s(),
                        group(
                            persist_encrypted_file_storage_id_task.s(archive),
                            calculate_checksum.signature_encrypted_file(archive),
                            calculate_size.signature_encrypted_file(archive),
                        ),
                    ),
                ),
            ),
        ),
        persist_processing_done.signature(archive),
    ).delay().forget()


@persisting_task(app, ArchiveCreationPersister)
def persist_plain_file_storage_id_task(
    persister: ArchiveCreationPersister, storage_id: ObjectId
):
    persister.set_plain_file_storage_id(storage_id)


@persisting_task(app, ArchiveCreationPersister)
def persist_encrypted_file_storage_id_task(
    persister: ArchiveCreationPersister, storage_id: ObjectId
):
    persister.set_encrypted_file_storage_id(storage_id)
