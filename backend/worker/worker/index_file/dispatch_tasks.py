import logging
from datetime import datetime
from uuid import UUID

from common.celery_app import TaskGroupName, task_group
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
)
from common.file.file_repository import File, Tag
from common.services.lazybytes_service import FileStorageLazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import IndexingPriority, UpdateFileRequest
from common.settings import settings
from common.utils.lucene import escape_lucene_phrase

from worker.index_file.infra.scan_query import (
    SCAN_RETRY_FOR,
    build_scan_query,
)

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
    max_recursion_depth: int = settings.indexing_max_recursion_depth,
    priority: IndexingPriority = IndexingPriority.MEDIUM,
) -> File:
    """Dispatch file for indexing."""
    return get_file_scheduling_service().index_file(
        full_name=full_name,
        file_content=file_content,
        source_id=source_id,
        parent_id=parent_id,
        uploaded_datetime=uploaded_datetime,
        recursion_depth=recursion_depth,
        max_recursion_depth=max_recursion_depth,
        priority=priority,
    )


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_reindex_files(
    query: QueryParameters,
    additional_recursion_depth: int,
    priority: IndexingPriority = IndexingPriority.MEDIUM,
):
    logger.info(
        "Dispatching tasks to reindex files with query '%s'"
        " (additional_recursion_depth: %s)",
        query,
        str(additional_recursion_depth),
    )
    file_repository = get_file_repository()
    for file in file_repository.get_id_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
        dispatch_reindex_file.s(
            file_id=file.id_,
            additional_recursion_depth=additional_recursion_depth,
            priority=priority,
        ).apply_async(priority=priority).forget()


@task_group(TaskGroupName.DISPATCH)
@app.task()
def dispatch_reindex_file(
    file_id: UUID,
    additional_recursion_depth: int,
    priority: IndexingPriority = IndexingPriority.MEDIUM,
):
    logger.info(
        "Dispatching tasks to reindex files with id '%s'"
        " (additional_recursion_depth: %s)",
        file_id,
        str(additional_recursion_depth),
    )
    get_file_scheduling_service().reindex_file(
        file_id=file_id,
        additional_recursion_depth=additional_recursion_depth,
        priority=priority,
    )


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_translate_files(query: QueryParameters, lang: str):
    logger.info("Dispatching tasks to translate files with query '%s'", query)
    file_repository = get_file_repository()
    for file in file_repository.get_id_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
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


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_update_for_files(query: QueryParameters, request: UpdateFileRequest):
    logger.info("dispatch request : '%s' for query: '%s'", request, query)
    # Only the id of each match is read, and the id generator is the one that asks
    # Elasticsearch for no more than that.
    file_repository = get_file_repository()
    for file in file_repository.get_id_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
        dispatch_update_for_file.s(file_id=file.id_, request=request).delay().forget()


@app.task()
def dispatch_update_for_file(file_id: UUID, request: UpdateFileRequest):
    logger.info("dispatch request: '%s' for id: '%s'", request, file_id)
    get_file_scheduling_service().update_file(file_id, request)


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_summarize_files(query: QueryParameters, system_prompt: str | None = None):
    logger.info("Dispatching tasks to summarize files with query '%s'", query)
    file_repository = get_file_repository()
    for file in file_repository.get_id_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
        dispatch_summarize_file.s(
            file_id=file.id_, system_prompt=system_prompt
        ).delay().forget()


@app.task()
def dispatch_summarize_file(file_id: UUID, system_prompt: str | None = None):
    logger.info("Dispatching tasks to summarize files with id '%s'", file_id)
    get_file_scheduling_service().summarize_file(
        file_id=file_id, system_prompt=system_prompt
    )


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_add_tags_to_files(
    query: QueryParameters,
    tags: list[Tag],
):
    logger.info("dispatch add tags tasks for tags %s and query: '%s'", tags, query)
    file_repository = get_file_repository()
    for file in file_repository.get_id_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
        dispatch_add_tags_to_file.s(file_id=file.id_, tags=tags).delay().forget()


@app.task()
def dispatch_add_tags_to_file(
    file_id: UUID,
    tags: list[Tag],
):
    logger.info("dispatch add tags tasks for tags %s and id: '%s'", tags, file_id)
    get_file_scheduling_service().add_tags(file_id=file_id, tags=tags)


@app.task(autoretry_for=SCAN_RETRY_FOR, retry_backoff=True)
def dispatch_remove_tag(
    tag: Tag,
):
    logger.info("dispatch remove tag: '%s' ", tag)
    # A tag is only length-constrained, so a quote or a backslash in one would
    # otherwise end the phrase and leave the sweep unable to find its files.
    query = QueryParameters(search_string=f'tags: "{escape_lucene_phrase(tag)}"')
    file_repository = get_file_repository()
    for file in file_repository.get_generator_by_query(
        query=build_scan_query(file_repository, query)
    ):
        dispatch_remove_tag_from_file.s(file_id=file.id_, tag=tag).delay().forget()


@app.task()
def dispatch_remove_tag_from_file(
    file_id: UUID,
    tag: Tag,
):
    logger.info("dispatch removing tag '%s' from file with id '%s'", tag, file_id)
    get_file_scheduling_service().remove_tag(file_id, tag)
