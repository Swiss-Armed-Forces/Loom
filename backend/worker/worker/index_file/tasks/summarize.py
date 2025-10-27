import logging

from celery import chain, chord
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service, get_ollama_client
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from httpx import HTTPError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ollama import Options

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE, TikaResult
from worker.settings import settings
from worker.utils.natural_language_detection import is_natural_language
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

MAX_SUMMARIZATION_INPUT_TEXT_LENGTH = TIKA_MAX_TEXT_SIZE

LLM_MAX_TOKENS_KEY_POINTS = 500
LLM_MAX_TOKENS_SUMMARIZE = 2000
LLM_MAX_TOKENS_SUMMARIZE_REFINE = 500

SUMMARIZE_MAX_RETRIES = 15


def signature(file: File) -> Signature:
    """Create the signature for summarization."""
    if settings.skip_summarize_while_indexing:
        return noop.s()

    return chain(
        extract_text_from_tika_result.s(),
        summarize_task.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(base=FileIndexingTask)
def extract_text_from_tika_result(tika_result: TikaResult) -> LazyBytes | None:
    return tika_result.text


def load_text_from_text_lazy(text_lazy: LazyBytes) -> str:
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
    text_lazy: LazyBytes | None,
    file: File,
    system_prompt: str | None = None,
):
    if text_lazy is None:
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.llm_summarize_text_chunk_size,
        chunk_overlap=settings.llm_summarize_text_chunk_overlap,
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
                persist_summary.s(file),
            ),
        )
    )


class LLMError(Exception):
    pass


def _invoke_llm(
    prompt: str,
    max_tokens: int = -1,
    system_prompt: str | None = None,
) -> str:
    if system_prompt is None:
        system_prompt = settings.llm_summarize_system_prompt

    client = get_ollama_client()
    try:
        response = client.generate(
            model=settings.llm_model,
            prompt=prompt,
            system=system_prompt,
            options=Options(
                temperature=settings.llm_temperature,
                num_predict=max_tokens,
            ),
            think=settings.llm_think,
        )
    except HTTPError as ex:
        raise LLMError() from ex
    return response.response


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=SUMMARIZE_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def extract_key_points(text: str) -> str:
    extract_prompt = f"""TEXT:
{text}

--------------------
PROMPT: Extract the KEY POINTS of the text above.
Return your response in a paragraph of {LLM_MAX_TOKENS_KEY_POINTS} tokens or less.
If there's nothing or not enough TEXT to extract key points just provide an empty answer.
Do NOT use any previous knowledge.

KEY POINTS:"""

    llm_response = _invoke_llm(
        prompt=extract_prompt, max_tokens=LLM_MAX_TOKENS_KEY_POINTS
    )
    return llm_response


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
    summarize_prompt = f"""TEXT:
{text}

--------------------
PROMPT: Write a concise SUMMARY of the TEXT above.
Return your response in a paragraph of {LLM_MAX_TOKENS_SUMMARIZE} tokens or less.
Do NOT explain that you are giving a summary, just output the summary.
If there's nothing or not enough TEXT to summarize just provide an empty answer.
Do NOT use any previous knowledge.

SUMMARY:"""

    llm_response = _invoke_llm(
        prompt=summarize_prompt, max_tokens=LLM_MAX_TOKENS_SUMMARIZE
    )
    return llm_response


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=SUMMARIZE_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def refine_summary(summary: str | None, system_prompt: str) -> str | None:
    if summary is None:
        return None
    refine_prompt = f"""TEXT:
{summary}

--------------------
PROMPT: Write a concise SUMMARY of the TEXT above.
Return your response in a paragraph of {LLM_MAX_TOKENS_SUMMARIZE_REFINE} tokens or less.
Do NOT explain that you are giving a summary, just output the summary.
If there's nothing or not enough TEXT to summarize just provide an empty answer.
Do NOT use any previous knowledge.

SUMMARY:"""

    llm_response = _invoke_llm(
        prompt=refine_prompt,
        max_tokens=LLM_MAX_TOKENS_SUMMARIZE_REFINE,
        system_prompt=system_prompt,
    )
    return llm_response


@persisting_task(app, IndexingPersister)
def persist_summary(
    persister: IndexingPersister,
    summary: str | None,
):
    if summary is None:
        return
    persister.set_summary(summary=summary)
