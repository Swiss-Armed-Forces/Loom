from uuid import UUID

from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.index_file.tasks.summarize import summarize_task

app = get_celery_app()


@app.task(bind=True, base=AiContextProcessingTask)
def summarize_file_tool_task(
    self: AiContextProcessingTask, file_id: str, _context_id: UUID
) -> str | None:
    file = get_file_repository().get_by_id(UUID(file_id))
    if file is None:
        raise LookupError(f"File {file_id} not found")
    content = file.content if file.content is not None else ""
    file_content = get_lazybytes_service().from_bytes(content.encode())
    return self.replace(summarize_task.s(file_content, file))
