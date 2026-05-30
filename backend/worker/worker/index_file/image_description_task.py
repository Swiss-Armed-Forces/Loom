import logging
from uuid import UUID

from celery import chain
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import (
    FileNotFoundException,
    FileWithoutStorageDataException,
)
from common.services.query_builder import QueryParameters

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import image_description

logger = logging.getLogger(__name__)
app = get_celery_app()


@app.task()
def dispatch_describe_images(query: QueryParameters, system_prompt: str | None = None):
    logger.info("Dispatching tasks to describe images with query '%s'", query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_describe_image.s(
            file_id=file.id_, system_prompt=system_prompt
        ).delay().forget()


@app.task()
def dispatch_describe_image(file_id: UUID, system_prompt: str | None = None):
    logger.info("Dispatching tasks to describe image with id '%s'", file_id)
    get_file_scheduling_service().describe_image(
        file_id=file_id, system_prompt=system_prompt
    )


@app.task(base=FileIndexingTask)
def image_description_task(file_id: UUID, system_prompt: str | None = None):
    """Task to trigger the image description of a file.

    Args:
        file_id: The ID of the file to describe.
        system_prompt: Optional system prompt to override the vision LLM default.
    """
    logger.info("Triggering image description for file %s", file_id)

    file_repository = get_file_repository()
    lazybytes_service = get_lazybytes_service()
    file_storage_service = get_file_storage_service()

    file = file_repository.get_by_id(file_id)
    if file is None:
        raise FileNotFoundException(f"File with id {file_id} not found")
    if file.storage_data is None:
        raise FileWithoutStorageDataException(
            f"File with id {file_id} has no storage data"
        )

    file_content = lazybytes_service.from_generator(
        file_storage_service.load_generator(file.storage_data)
    )

    # On-demand description is explicitly requested by the user, so we bypass
    # detection (pass is_image_detected=True) and describe the file directly.
    chain(
        image_description.describe_image_task.s(
            True, file_content, file, system_prompt
        ),
        image_description.persist_image_description_task.s(file.id_),
    ).apply_async()
