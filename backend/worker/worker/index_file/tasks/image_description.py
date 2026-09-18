import logging

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_llm_vision_agent,
)
from common.file.file_repository import File
from common.services.lazybytes_service import TempLazyBytes
from common.settings import settings
from common.utils.cache import cache
from pydantic import BaseModel
from pydantic_ai import NativeOutput
from pydantic_ai.messages import BinaryContent

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.settings import settings as worker_settings
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


IMAGE_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
]
IMAGE_MIMETYPES = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
]


class LLMError(Exception):
    pass


class _ImageDescriptionResult(BaseModel):
    description: str


def is_image(extension: str, mimetype: str) -> bool:
    return extension in IMAGE_EXTENSIONS or mimetype in IMAGE_MIMETYPES


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


def signature(file_content: TempLazyBytes, file: File) -> Signature:
    if worker_settings.skip_image_description_while_indexing:
        return noop.s()

    return chain(
        detect_image_task.s(file.extension),
        describe_image_task.s(file_content, file),
        persist_image_description_task.s(file.id_),
    )


DESCRIBE_IMAGE_MAX_RETRIES = 15


def describe_image(data: memoryview, system_prompt: str | None = None) -> str:
    prompt = f"""PROMPT: Describe the contents of the image in detail.
Include any visible text, objects, people, scenes, colors, and layout.
Do NOT use any prior knowledge — only describe what is visible in the image.
Respond with a description of at most {settings.llm.vision.max_sentences} sentences.

DESCRIPTION:"""

    agent = get_llm_vision_agent()

    # Augment with user prompt addition, if set
    if system_prompt is not None:
        prompt += "\n\n" + system_prompt

    try:
        result = agent.run_sync(
            [
                prompt,
                BinaryContent(
                    data=bytes(data),
                    media_type="image/jpeg",
                ),
            ],
            output_type=NativeOutput(_ImageDescriptionResult),
        )

    except Exception as ex:
        raise LLMError("Image description failed") from ex

    return result.output.description


@app.task(base=FileIndexingTask)
def detect_image_task(file_type: str, file_extension: str) -> bool:
    return is_image(extension=file_extension, mimetype=file_type)


@app.task(
    base=FileIndexingTask,
    autoretry_for=(LLMError,),
    max_retries=DESCRIBE_IMAGE_MAX_RETRIES,
    retry_backoff=True,
)
@cache(
    key_function=lambda is_image_detected, _, file, system_prompt=None: (
        is_image_detected,
        file.sha256,
        system_prompt,
    )
)
def describe_image_task(
    is_image_detected: bool,
    file_content: TempLazyBytes,
    _: File,
    system_prompt: str | None = None,
) -> str | None:
    if not is_image_detected:
        return None
    with get_lazybytes_service().load_memoryview(file_content) as memview:
        return describe_image(memview, system_prompt=system_prompt)


@persisting_task(app, IndexingPersister)
def persist_image_description_task(
    persister: IndexingPersister, image_description: str | None
):
    if image_description is None:
        return
    persister.set_image_description(image_description)
