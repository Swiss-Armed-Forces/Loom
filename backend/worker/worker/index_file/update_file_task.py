import logging
from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import persist_processing_done
from worker.index_file.tasks.update_file import update_file

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task()
def dispatch_update_for_files(query: QueryParameters, request: UpdateFileRequest):
    logger.info("dispatch request : '%s' for query: '%s'", request, query)
    for file in get_file_repository().get_generator_by_query(query=query):
        dispatch_update_for_file.s(file_id=file.id_, request=request).delay().forget()


@app.task()
def dispatch_update_for_file(file_id: UUID, request: UpdateFileRequest):
    logger.info("dispatch request: '%s' for id: '%s'", request, file_id)
    get_file_scheduling_service().update_file(file_id, request)


@app.task(base=FileIndexingTask)
def update_task(file_id: UUID, request: UpdateFileRequest):
    logger.info("updating request: '%s' for id '%s'", request, file_id)
    chain(
        update_file.s(request, file_id),
        persist_processing_done.signature(file_id),
    ).delay().forget()
