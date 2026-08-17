from uuid import UUID

from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.index_file.tasks.translate import DetectedLanguage, translate_task
from worker.index_file.translate_file_task import ON_DEMAND_TRANSLATION_CONFIDENCE

app = get_celery_app()


@app.task(bind=True, base=AiContextProcessingTask)
def translate_file_tool_task(
    self: AiContextProcessingTask, file_id: str, language: str, _context_id: UUID
) -> None:
    file = get_file_repository().get_by_id(UUID(file_id))
    if file is None:
        raise LookupError(f"File {file_id} not found")
    detected_language = DetectedLanguage(
        confidence=ON_DEMAND_TRANSLATION_CONFIDENCE, language=language
    )
    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    return self.replace(translate_task.s((file_content, [detected_language]), file))
