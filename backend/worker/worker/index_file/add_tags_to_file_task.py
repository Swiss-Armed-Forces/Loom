import logging
from uuid import UUID

from common.dependencies import get_celery_app
from common.file.file_repository import Tag

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.persist_tags import persist_add_tags

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def add_tags_to_file_task(file_id: UUID, tags: list[Tag]):
    logger.info("adding tag to file with id '%s'", file_id)

    persist_add_tags.s(tags, file_id).delay().forget()
