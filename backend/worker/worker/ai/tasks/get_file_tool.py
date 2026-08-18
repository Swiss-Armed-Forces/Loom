from uuid import UUID

from common.ai_context.tool_models import (
    GetFileFieldResult,
    GetFileResult,
)
from common.dependencies import get_celery_app, get_file_repository
from common.file.file_repository import File
from common.utils.pydantic_field_paths import traverse_attr_path

from worker.ai.file_fields import (
    iter_described_fields,
    serialize_field_value,
    validate_file_id,
)
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask

app = get_celery_app()


@app.task(base=AiContextProcessingTask)
def get_file_work_task(file_id: str) -> GetFileResult:
    file_uuid = validate_file_id(file_id)
    file = get_file_repository().get_by_id(file_uuid)
    if file is None:
        raise LookupError(f"File not found: {file_id}")

    available_fields = [
        field
        for field in iter_described_fields(File)
        if traverse_attr_path(file, field.name) is not None
    ]

    return GetFileResult(
        file_id=str(file.id_),
        full_path=str(file.full_path),
        available_fields=available_fields,
    )


@app.task(bind=True, base=AiContextProcessingTask)
def get_file_tool_task(
    self: AiContextProcessingTask, file_id: str, _context_id: UUID
) -> GetFileResult:
    return self.replace(get_file_work_task.s(file_id))


@app.task(base=AiContextProcessingTask)
def get_file_field_work_task(file_id: str, field: str) -> GetFileFieldResult:
    file_uuid = validate_file_id(file_id)

    known = {f.name for f in iter_described_fields(File)}
    if field not in known:
        raise ValueError(f"Unknown field '{field}'. Valid fields: {sorted(known)}")

    file = get_file_repository().get_by_id(file_uuid)
    if file is None:
        raise LookupError(f"File not found: {file_id}")

    raw_value = traverse_attr_path(file, field)
    if raw_value is None:
        raise LookupError(f"Field '{field}' is not available for file {file_id}")

    value = serialize_field_value(field, raw_value)

    return GetFileFieldResult(
        file_id=str(file.id_),
        field=field,
        value=value,
    )


@app.task(bind=True, base=AiContextProcessingTask)
def get_file_field_tool_task(
    self: AiContextProcessingTask, file_id: str, field: str, _context_id: UUID
) -> GetFileFieldResult:
    return self.replace(get_file_field_work_task.s(file_id, field))
