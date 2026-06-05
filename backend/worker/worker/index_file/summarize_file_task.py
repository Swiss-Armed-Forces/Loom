import logging
from uuid import UUID

from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)
from common.file.file_repository import FileNotFoundException

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.summarize import summarize_task

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def summarize_file_task(file_id: UUID, system_prompt: str | None = None):
    logger.info("Summarizing file with id '%s'", file_id)

    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("No file found")

    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    summarize_task.s(
        text_lazy=file_content,
        file=file,
        system_prompt=system_prompt,
    ).delay().forget()
