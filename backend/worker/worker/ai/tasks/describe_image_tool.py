from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_storage_service,
    get_lazybytes_service,
)

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.index_file.tasks import image_description

app = get_celery_app()


@app.task(bind=True, base=AiContextProcessingTask)
def describe_image_tool_task(
    self: AiContextProcessingTask, file_id: str, _context_id: UUID
) -> str | None:
    file = get_file_repository().get_by_id(UUID(file_id))
    if file is None:
        raise LookupError(f"File {file_id} not found")
    if file.storage_data is None:
        raise LookupError(f"File {file_id} has no storage data")
    file_content = get_lazybytes_service().from_generator(
        get_file_storage_service().load_generator(file.storage_data)
    )
    return self.replace(
        chain(
            image_description.describe_image_task.s(True, file_content, file, None),
            image_description.persist_image_description_task.s(file.id_),
        )
    )
