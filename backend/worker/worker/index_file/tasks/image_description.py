import base64
import logging

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_llm_vision_client,
)
from common.file.file_repository import File
from common.services.lazybytes_service import TempLazyBytes
from common.settings import settings
from common.utils.cache import cache
from openai import APIError
from pydantic import BaseModel

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.settings import settings as worker_settings
from worker.utils.persisting_task import persisting_task
from worker.utils.prompt_sanitizer import build_document_security_instructions

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


class ImageDescriptionError(Exception):
    pass


class _ImageDescriptionResult(BaseModel):
    description: str


def describe_image(data: memoryview, system_prompt: str | None = None) -> str:
    prompt = f"""PROMPT: Describe the contents of the image in detail.
Include any visible text, objects, people, scenes, colors, and layout.
Do NOT use any prior knowledge — only describe what is visible in the image.
Respond with a description of at most {settings.llm.vision.max_tokens} tokens.

DESCRIPTION:"""
    resolved_system_prompt = (
        f"{settings.llm.vision.system_prompt}\n\n"
        f"{build_document_security_instructions(settings.translate_target)}"
    )
    if system_prompt is not None:
        resolved_system_prompt = f"{resolved_system_prompt}\n\n{system_prompt}"

    client = get_llm_vision_client()

    image = base64.b64encode(data).decode(errors=settings.decode_error_handler)

    try:
        response = client.beta.chat.completions.parse(
            model=settings.llm.vision.model,
            messages=[
                {"role": "system", "content": resolved_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            # Ollama detects the real image format from the
                            # decoded bytes, so the data-URL media type is
                            # nominal.
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        },
                    ],
                },
            ],
            temperature=settings.llm.vision.temperature,
            extra_headers=settings.llm.vision.extra_headers,
            extra_body=settings.llm.vision.extra_body,
            response_format=_ImageDescriptionResult,
        )
    except APIError as ex:
        raise ImageDescriptionError() from ex

    result = response.choices[0].message.parsed
    return settings.llm.vision.truncate_response(
        result.description if result is not None else ""
    )


@app.task(base=FileIndexingTask)
def detect_image_task(file_type: str, file_extension: str) -> bool:
    return is_image(extension=file_extension, mimetype=file_type)


@app.task(
    base=FileIndexingTask,
    autoretry_for=(ImageDescriptionError,),
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
