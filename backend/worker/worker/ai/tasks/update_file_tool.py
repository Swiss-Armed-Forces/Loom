from uuid import UUID

from common.dependencies import get_celery_app, get_file_repository
from common.services.task_scheduling_service import UpdateFileRequest

from worker.ai.file_fields import validate_file_id
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.index_file.tasks.update_file import update_file

app = get_celery_app()


@app.task(bind=True, base=AiContextProcessingTask)
def update_file_tool_task(
    self: AiContextProcessingTask,
    file_id: str,
    request: UpdateFileRequest,
    _context_id: UUID,
) -> UpdateFileRequest:
    """Set the seen, flagged and hidden flags of one file and return what was set.

    The file is looked up before the write is handed on so that a file id the model
    invented is reported as a missing file rather than as a mutation of nothing.
    """
    file_uuid = validate_file_id(file_id)
    if get_file_repository().get_by_id(file_uuid) is None:
        raise LookupError(f"File {file_id} not found")
    return self.replace(update_file.s(request, file_uuid))
