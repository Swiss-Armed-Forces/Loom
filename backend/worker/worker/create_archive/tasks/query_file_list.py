import logging
from typing import List

from common.dependencies import get_celery_app, get_file_repository
from common.file.file_repository import File
from common.services.query_builder import QueryParameters

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def query_file_list_for_archive_task(query: QueryParameters) -> List[File]:
    query.search_string = f"({query.search_string}) AND exclude_from_archives:false"
    files = list(get_file_repository().get_generator_by_query(query=query))
    logger.info("Creating archive containing %d files", len(files))
    return files
