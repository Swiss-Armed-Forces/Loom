from uuid import UUID

from celery import chain
from common.dependencies import get_file_repository, get_file_scheduling_service
from common.services.query_builder import QueryParameters

from worker.index_file.add_tags_to_file_task import FileNotFoundException, app, logger
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import persist_processing_done
from worker.index_file.tasks.persist_tags import persist_remove_tag


@app.task()
def dispatch_remove_tag(
    tag: str,
):
    logger.info("dispatch remove tag: '%s' ", tag)
    file_repository = get_file_repository()
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(), search_string=f'tags: "{tag}"'
    )
    for file in file_repository.get_generator_by_query(query=query):
        dispatch_remove_tag_from_file.s(file_id=file.id_, tag=tag).delay().forget()


@app.task()
def dispatch_remove_tag_from_file(
    file_id: UUID,
    tag: str,
):
    logger.info("dispatch removing tag '%s' from file with id '%s'", tag, file_id)
    get_file_scheduling_service().remove_tag(file_id, tag)


@app.task(base=FileIndexingTask)
def remove_tag_from_file_task(file_id: UUID, tag: str):
    logger.info("removing tag '%s' from file with id '%s'", tag, file_id)
    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("no file found")

    chain(
        persist_remove_tag.s(tag, file), persist_processing_done.signature(file)
    ).delay().forget()
