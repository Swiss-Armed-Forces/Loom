import logging
from datetime import datetime
from uuid import UUID

from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
)
from common.file.file_repository import File, Tag
from common.services.celery_inspect_service import TaskGroupName, task_group
from common.services.lazybytes_service import FileStorageLazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

logger = logging.getLogger(__name__)

app = get_celery_app()


@task_group(TaskGroupName.DISPATCH)
@app.task()
# pylint: disable=too-many-arguments, too-many-positional-arguments
def dispatch_index_file(
    full_name: str,
    file_content: FileStorageLazyBytes,
    source_id: str,
    parent_id: UUID | None = None,
    uploaded_datetime: datetime | None = None,
    recursion_depth: int = 0,
) -> File:
    """Dispatch file for indexing."""
    return get_file_scheduling_service().index_file(
        full_name=full_name,
        file_content=file_content,
        source_id=source_id,
        parent_id=parent_id,
        uploaded_datetime=uploaded_datetime,
        recursion_depth=recursion_depth,
    )


@app.task()
def dispatch_reindex_files(query: QueryParameters):
    logger.info("Dispatching tasks to reindex files with query '%s'", query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_reindex_file.s(file_id=file.id_).delay().forget()


@task_group(TaskGroupName.DISPATCH)
@app.task()
def dispatch_reindex_file(file_id: UUID):
    logger.info("Dispatching tasks to reindex files with id '%s'", file_id)
    get_file_scheduling_service().reindex_file(file_id=file_id)


@app.task()
def dispatch_translate_files(query: QueryParameters, lang: str):
    logger.info("Dispatching tasks to translate files with query '%s'", query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_translate_file.s(
            file_id=file.id_,
            lang=lang,
        ).delay().forget()


@app.task()
def dispatch_translate_file(file_id: UUID, lang: str):
    logger.info("Dispatching tasks to translate files with id '%s'", file_id)
    get_file_scheduling_service().translate_file(
        file_id=file_id,
        lang=lang,
    )


@app.task()
def dispatch_update_for_files(query: QueryParameters, request: UpdateFileRequest):
    logger.info("dispatch request : '%s' for query: '%s'", request, query)
    for file in get_file_repository().get_generator_by_query(query=query):
        dispatch_update_for_file.s(file_id=file.id_, request=request).delay().forget()


@app.task()
def dispatch_update_for_file(file_id: UUID, request: UpdateFileRequest):
    logger.info("dispatch request: '%s' for id: '%s'", request, file_id)
    get_file_scheduling_service().update_file(file_id, request)


@app.task()
def dispatch_summarize_files(query: QueryParameters, system_prompt: str | None = None):
    logger.info("Dispatching tasks to summarize files with query '%s'", query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_summarize_file.s(
            file_id=file.id_, system_prompt=system_prompt
        ).delay().forget()


@app.task()
def dispatch_summarize_file(file_id: UUID, system_prompt: str | None = None):
    logger.info("Dispatching tasks to summarize files with id '%s'", file_id)
    get_file_scheduling_service().summarize_file(
        file_id=file_id, system_prompt=system_prompt
    )


@app.task()
def dispatch_add_tags_to_files(
    query: QueryParameters,
    tags: list[Tag],
):
    logger.info("dispatch add tags tasks for tags %s and query: '%s'", tags, query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_add_tags_to_file.s(file_id=file.id_, tags=tags).delay().forget()


@app.task()
def dispatch_add_tags_to_file(
    file_id: UUID,
    tags: list[Tag],
):
    logger.info("dispatch add tags tasks for tags %s and id: '%s'", tags, file_id)
    get_file_scheduling_service().add_tags(file_id=file_id, tags=tags)


@app.task()
def dispatch_remove_tag(
    tag: Tag,
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
    tag: Tag,
):
    logger.info("dispatch removing tag '%s' from file with id '%s'", tag, file_id)
    get_file_scheduling_service().remove_tag(file_id, tag)
