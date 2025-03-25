import logging
from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
    get_lazybytes_service,
)
from common.file.file_repository import FileNotFoundException
from common.services.query_builder import QueryParameters

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import persist_processing_done
from worker.index_file.tasks.summarize import summarize_task

logger = logging.getLogger(__name__)

app = get_celery_app()


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


@app.task(base=FileIndexingTask)
def summarize_file_task(file_id: UUID, system_prompt: str | None = None):
    logger.info("Summarizing file with id '%s'", file_id)

    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("No file found")

    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    chain(
        summarize_task.s(
            text_lazy=file_content,
            file=file,
            system_prompt=system_prompt,
        ),
        persist_processing_done.signature(file),
    ).delay().forget()
