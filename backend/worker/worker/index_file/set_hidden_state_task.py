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
from worker.index_file.tasks.persist_file import persist_files_hidden_state


class FileNotFoundException(BaseException):
    pass


logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task()
def dispatch_set_hidden_state_for_files(query: QueryParameters, hidden: bool):
    logger.info("dispatch set hidden state: '%s' for query: '%s'", hidden, query)
    for file in get_file_repository().get_generator_by_query(query=query):
        dispatch_set_hidden_state_for_file.s(
            file_id=file.id_, hidden=hidden
        ).delay().forget()


@app.task()
def dispatch_set_hidden_state_for_file(file_id: UUID, hidden: bool):
    logger.info("dispatch set hidden state: '%s' for id: '%s'", hidden, file_id)
    get_file_scheduling_service().set_hidden_state(file_id, hidden)


@app.task(base=FileIndexingTask)
def set_hidden_state_task(file_id: UUID, hidden: bool):
    logger.info("updating file hidden state with id '%s'", file_id)
    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("No file found")

    chain(
        persist_files_hidden_state.s(hidden, file),
        persist_processing_done.signature(file),
    ).delay().forget()
