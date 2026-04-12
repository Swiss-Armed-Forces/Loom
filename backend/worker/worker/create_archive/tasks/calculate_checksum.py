import hashlib
from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
)
from common.services.lazybytes_service import LazyBytes

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature_plain_file(archive_id: UUID):
    return chain(
        calculate_checksum_task.s(),
        persist_checksum_plain_file_task.s(archive_id),
    )


def signature_encrypted_file(archive_id: UUID):
    return chain(
        calculate_checksum_task.s(),
        persist_checksum_encrypted_file_task.s(archive_id),
    )


@app.task(base=ArchiveProcessingTask)
def calculate_checksum_task(storage_data: LazyBytes) -> str:
    checksum = hashlib.sha256()
    for chunk in get_file_storage_service().load_generator(storage_data):
        checksum.update(chunk)
    return checksum.hexdigest()


@persisting_task(app, ArchiveCreationPersister)
def persist_checksum_plain_file_task(
    persister: ArchiveCreationPersister, checksums: str
):
    persister.set_plain_file_checksum(checksums)


@persisting_task(app, ArchiveCreationPersister)
def persist_checksum_encrypted_file_task(
    persister: ArchiveCreationPersister, checksums: str
):
    persister.set_encrypted_file_checksum(checksums)
