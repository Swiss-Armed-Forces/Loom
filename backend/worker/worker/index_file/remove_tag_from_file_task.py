import logging
from uuid import UUID

from common.dependencies import get_celery_app
from common.file.file_repository import Tag

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.persist_tags import persist_remove_tag

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def remove_tag_from_file_task(file_id: UUID, tag: Tag):
    logger.info("removing tag '%s' from file with id '%s'", tag, file_id)
    persist_remove_tag.s(tag, file_id).delay().forget()
