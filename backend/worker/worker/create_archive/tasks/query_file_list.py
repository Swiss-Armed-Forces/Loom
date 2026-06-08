import logging
from typing import List
from uuid import UUID

from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)
from common.services.lazybytes_service import TempTypedLazyBytes
from common.services.query_builder import QueryParameters

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

logger = logging.getLogger(__name__)

app = get_celery_app()

FileIdList = List[UUID]


@app.task(base=ArchiveProcessingTask)
def query_file_list_for_archive_task(
    query: QueryParameters,
) -> TempTypedLazyBytes[FileIdList]:
    file_ids: FileIdList = [
        obj.id_ for obj in get_file_repository().get_id_generator_by_query(query=query)
    ]
    logger.info("Creating archive containing %d files", len(file_ids))
    return get_lazybytes_service().from_object(file_ids)
