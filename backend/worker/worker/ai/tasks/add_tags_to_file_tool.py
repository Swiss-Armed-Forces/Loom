from uuid import UUID

from common.dependencies import get_celery_app, get_file_repository
from common.file.file_repository import Tag

from worker.ai.file_fields import validate_file_id
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.index_file.tasks.persist_tags import persist_add_tags

app = get_celery_app()


@app.task(bind=True, base=AiContextProcessingTask)
def add_tags_to_file_tool_task(
    self: AiContextProcessingTask,
    file_id: str,
    tags: list[Tag],
    _context_id: UUID,
) -> list[Tag]:
    """Add tags to one file and return the tags that were written.

    The file is looked up before the write is handed on so that a file id the model
    invented is reported as a missing file rather than as a mutation of nothing.
    """
    file_uuid = validate_file_id(file_id)
    if get_file_repository().get_by_id(file_uuid) is None:
        raise LookupError(f"File {file_id} not found")
    return self.replace(persist_add_tags.s(tags, file_uuid))
