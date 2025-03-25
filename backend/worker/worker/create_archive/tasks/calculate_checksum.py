import hashlib

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


def signature_plain_file(archive: Archive):
    return chain(
        calculate_checksum_task.s(),
        persist_checksum_plain_file_task.s(archive),
    )


def signature_encrypted_file(archive: Archive):
    return chain(
        calculate_checksum_task.s(),
        persist_checksum_encrypted_file_task.s(archive),
    )


@app.task(base=ArchiveProcessingTask)
def calculate_checksum_task(storage_id: ObjectId) -> str:
    checksum = hashlib.sha256()
    for chunk in get_file_storage_service().open_download_iterator(storage_id):
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
