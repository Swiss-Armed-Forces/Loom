from bson import ObjectId
from celery import chain
from common.archive.archive_repository import Archive
from common.dependencies import get_celery_app, get_file_storage_service

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature_plain_file(archive_info: Archive):
    return chain(
        calculate_size_task.s(),
        persist_size_plain_file_task.s(archive_info),
    )


def signature_encrypted_file(archive_info: Archive):
    return chain(
        calculate_size_task.s(),
        persist_size_encrypted_file_task.s(archive_info),
    )


@app.task(base=ArchiveProcessingTask)
def calculate_size_task(storage_id: ObjectId) -> int:
    size = 0
    for chunk in get_file_storage_service().open_download_iterator(storage_id):
        size += len(chunk)
    return size


@persisting_task(app, ArchiveCreationPersister)
def persist_size_plain_file_task(persister: ArchiveCreationPersister, size: int):
    persister.set_plain_file_size(size)


@persisting_task(app, ArchiveCreationPersister)
def persist_size_encrypted_file_task(persister: ArchiveCreationPersister, size: int):
    persister.set_encrypted_file_size(size)
