import logging
from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
)
from common.services.query_builder import QueryParameters

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import persist_processing_done
from worker.index_file.tasks.persist_tags import persist_add_tags


class FileNotFoundException(BaseException):
    pass


logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task()
def dispatch_add_tags_to_files(
    query: QueryParameters,
    tags: list[str],
):
    logger.info("dispatch add tags tasks for tags %s and query: '%s'", tags, query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_add_tags_to_file.s(file_id=file.id_, tags=tags).delay().forget()


@app.task()
def dispatch_add_tags_to_file(
    file_id: UUID,
    tags: list[str],
):
    logger.info("dispatch add tags tasks for tags %s and id: '%s'", tags, file_id)
    get_file_scheduling_service().add_tags(file_id=file_id, tags=tags)


@app.task(base=FileIndexingTask)
def add_tags_to_file_task(file_id: UUID, tags: list[str]):
    logger.info("adding tag to file with id '%s'", file_id)
    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("no file found")

    chain(
        persist_add_tags.s(tags, file), persist_processing_done.signature(file)
    ).delay().forget()
