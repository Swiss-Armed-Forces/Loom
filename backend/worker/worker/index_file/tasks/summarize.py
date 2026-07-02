import logging

from celery import chain, chord
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_llm_summarization_client,
    get_llm_summarization_key_points_client,
    get_llm_summarization_refine_client,
)
from common.file.file_repository import File
from common.services.lazybytes_service import TempLazyBytes
from common.settings import LLMSummarizationBaseSettings
from common.utils.cache import cache
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import APIError, OpenAI
from pydantic import BaseModel

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE
from worker.settings import settings
from worker.utils.natural_language_detection import is_natural_language
from worker.utils.persisting_task import persisting_task
from worker.utils.prompt_sanitizer import (
    build_document_security_instructions,
    sanitize_document_text,
)

logger = logging.getLogger(__name__)

app = get_celery_app()

MAX_SUMMARIZATION_INPUT_TEXT_LENGTH = TIKA_MAX_TEXT_SIZE

SUMMARIZE_MAX_RETRIES = 15


def signature(file: File) -> Signature:
    """Create the signature for summarization."""
    if settings.skip_summarize_while_indexing:
        return noop.s()

    return chain(
        summarize_task.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


def load_text_from_text_lazy(text_lazy: TempLazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_SUMMARIZATION_INPUT_TEXT_LENGTH]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        return text


@app.task(bind=True, base=FileIndexingTask)
def summarize_task(
    self: FileIndexingTask,
    text_lazy: TempLazyBytes | None,
    file: File,
    system_prompt: str | None = None,
):
    if text_lazy is None:
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.llm.summarization_key_points.text_chunk_size,
        chunk_overlap=settings.llm.summarization_key_points.text_chunk_overlap,
    )
    text = load_text_from_text_lazy(text_lazy)

    text_chunks = text_splitter.split_text(text)
    return self.replace(
        chord(
            [
                extract_key_points.s(text_chunk)
                for text_chunk in text_chunks
                if is_natural_language(text_chunk)
            ],
            chain(
                summarize.s(),
                refine_summary.s(system_prompt),
                persist_summary.s(file.id_),
            ),
        )
    )


class LLMError(Exception):
    pass


class _SummarizationResult(BaseModel):
    text: str


def _invoke_llm(
    prompt: str,
    llm_settings: LLMSummarizationBaseSettings,
    client: OpenAI,
    system_prompt: str | None = None,
) -> str:
    resolved_system_prompt = (
        f"{llm_settings.system_prompt}\n\n"
        f"{build_document_security_instructions(settings.translate_target)}"
    )
    if system_prompt is not None:
        resolved_system_prompt = f"{resolved_system_prompt}\n\n{system_prompt}"
    try:
        response = client.beta.chat.completions.parse(
            model=llm_settings.model,
            messages=[
                {"role": "system", "content": resolved_system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=llm_settings.temperature,
            extra_headers=llm_settings.extra_headers,
            extra_body=llm_settings.extra_body,
            response_format=_SummarizationResult,
        )
    except APIError as ex:
        raise LLMError() from ex
    result = response.choices[0].message.parsed
    return result.text if result is not None else ""


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=SUMMARIZE_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def extract_key_points(text: str) -> str:
    sanitized_text = sanitize_document_text(text)
    extract_prompt = f"""<document>
{sanitized_text}
</document>

Extract the KEY POINTS of the document above.
Return your response in a paragraph of
{settings.llm.summarization_key_points.max_tokens} tokens or less.
If there's nothing or not enough content to extract key points just provide an empty answer.
Do NOT use any previous knowledge.

KEY POINTS:"""

    return settings.llm.summarization_key_points.truncate_response(
        _invoke_llm(
            extract_prompt,
            settings.llm.summarization_key_points,
            get_llm_summarization_key_points_client(),
        )
    )


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=SUMMARIZE_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def summarize(key_points: list[str]) -> str | None:
    if len(key_points) <= 0:
        return None
    # We reverse here the key points so that that key points from the
    # beginning of the document come last and are therefore more
    # relevant in the context window
    text = "\n".join(reversed(key_points))
    sanitized_text = sanitize_document_text(text)
    summarize_prompt = f"""<document>
{sanitized_text}
</document>

Write a concise SUMMARY of the document above.
Return your response in a paragraph of {settings.llm.summarization.max_tokens} tokens or less.
Do NOT explain that you are giving a summary, just output the summary.
If there's nothing or not enough content to summarize just provide an empty answer.
Do NOT use any previous knowledge.

SUMMARY:"""

    return settings.llm.summarization.truncate_response(
        _invoke_llm(
            summarize_prompt,
            settings.llm.summarization,
            get_llm_summarization_client(),
        )
    )


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=SUMMARIZE_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def refine_summary(summary: str | None, system_prompt: str | None) -> str | None:
    if summary is None:
        return None
    sanitized_summary = sanitize_document_text(summary)
    refine_prompt = f"""<document>
{sanitized_summary}
</document>

Write a concise SUMMARY of the document above.
Return your response in a paragraph of
{settings.llm.summarization_refine.max_tokens} tokens or less.
Do NOT explain that you are giving a summary, just output the summary.
If there's nothing or not enough content to summarize just provide an empty answer.
Do NOT use any previous knowledge.

SUMMARY:"""

    return settings.llm.summarization_refine.truncate_response(
        _invoke_llm(
            refine_prompt,
            settings.llm.summarization_refine,
            get_llm_summarization_refine_client(),
            system_prompt=system_prompt,
        )
    )


@persisting_task(app, IndexingPersister)
def persist_summary(
    persister: IndexingPersister,
    summary: str | None,
):
    if summary is None:
        return
    persister.set_summary(summary=summary)
