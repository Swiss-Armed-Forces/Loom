from uuid import UUID

from common.dependencies import (
    get_archive_repository,
    get_celery_app,
    get_lazybytes_service,
)
from common.services.lazybytes_service import TempTypedLazyBytes

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks.query_file_list import FileIdList
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def link_files_with_archive(
    lazy_file_ids: TempTypedLazyBytes[FileIdList], archive_id: UUID
) -> TempTypedLazyBytes[FileIdList]:
    file_ids = get_lazybytes_service().load_object(lazy_file_ids)
    for file_id in file_ids:
        persist_file_to_archive_link.s(archive_id, file_id).delay().forget()
    return lazy_file_ids


@persisting_task(app, IndexingPersister, get_archive_repository)
def persist_file_to_archive_link(persister: IndexingPersister, archive_id: UUID):
    persister.add_archive(archive_id)
