import logging
from uuid import UUID

from celery import chain, group
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
from worker.index_file.tasks.translate import (
    LibretranslateDetectedLanguage,
    persist_best_detected_language,
    translate_task,
)

logger = logging.getLogger(__name__)

app = get_celery_app()

ON_DEMAND_TRANSLATION_CONFIDENCE = 100.0


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


@app.task(base=FileIndexingTask)
def translate_file_task(lang: str, file_id: UUID):
    logger.info("Translating file with id '%s'", file_id)

    file = get_file_repository().get_by_id(file_id)
    if file is None:
        raise FileNotFoundException("No file found")
    libretranslate_language = LibretranslateDetectedLanguage(
        confidence=ON_DEMAND_TRANSLATION_CONFIDENCE, language=lang
    )
    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    chain(
        group(
            translate_task.s((file_content, [libretranslate_language]), file),
            persist_best_detected_language.s(libretranslate_language.language, file),
        ),
        persist_processing_done.signature(file),
    ).delay().forget()
