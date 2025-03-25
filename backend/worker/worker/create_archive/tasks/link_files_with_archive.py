from typing import List
from uuid import UUID

from common.dependencies import get_archive_repository, get_celery_app
from common.file.file_repository import File

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def link_files_with_archive(files: List[File], archive_id: UUID):
    for file in files:
        persist_file_to_archive_link.s(archive_id, file).delay().forget()


@persisting_task(app, IndexingPersister, get_archive_repository)
def persist_file_to_archive_link(persister: IndexingPersister, archive_id: UUID):
    persister.add_archive(archive_id)
