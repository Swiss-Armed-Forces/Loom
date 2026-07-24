import logging
from uuid import UUID

from celery import group
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)
from common.file.file_repository import FileNotFoundException

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.translate import (
    DetectedLanguage,
    persist_best_detected_language,
    translate_task,
)

logger = logging.getLogger(__name__)

app = get_celery_app()

ON_DEMAND_TRANSLATION_CONFIDENCE = 100.0


@app.task(base=FileIndexingTask)
def translate_file_task(lang: str, file_id: UUID):
    logger.info("Translating file with id '%s'", file_id)
    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("No file found")
    detected_language = DetectedLanguage(
        confidence=ON_DEMAND_TRANSLATION_CONFIDENCE, language=lang
    )
    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    group(
        translate_task.s((file_content, [detected_language]), file),
        persist_best_detected_language.s(detected_language.language, file_id),
    ).delay().forget()
