from uuid import UUID

from celery import chain
from common.dependencies import get_celery_app, get_file_storage_service
from common.services.lazybytes_service import LazyBytes

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature_plain_file(archive_id: UUID):
    return chain(
        calculate_size_task.s(),
        persist_size_plain_file_task.s(archive_id),
    )


def signature_encrypted_file(archive_id: UUID):
    return chain(
        calculate_size_task.s(),
        persist_size_encrypted_file_task.s(archive_id),
    )


@app.task(base=ArchiveProcessingTask)
def calculate_size_task(storage_data: LazyBytes) -> int:
    size = 0
    for chunk in get_file_storage_service().load_generator(storage_data):
        size += len(chunk)
    return size


@persisting_task(app, ArchiveCreationPersister)
def persist_size_plain_file_task(persister: ArchiveCreationPersister, size: int):
    persister.set_plain_file_size(size)


@persisting_task(app, ArchiveCreationPersister)
def persist_size_encrypted_file_task(persister: ArchiveCreationPersister, size: int):
    persister.set_encrypted_file_size(size)
