# pylint: disable=duplicate-code
import logging

from celery import chain, chord
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service, get_ollama_client
from common.file.file_repository import Embedding, File
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from httpx import HTTPError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ollama import Options
from pydantic_core import from_json, to_json

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TikaResult
from worker.settings import settings
from worker.utils.async_task_branch import complete_async_branch
from worker.utils.natural_language_detection import is_natural_language
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

CHUNK_LENGTH = 400
CHUNK_OVERLAP = 100

CREATE_EMBEDDING_MAX_RETRIES = 15


def signature(file: File) -> Signature:
    """Create the signature for vectorization."""
    return chain(
        extract_text_from_tika_result.s(),
        create_embedding_task.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(base=FileIndexingTask)
def extract_text_from_tika_result(tika_result: TikaResult) -> LazyBytes | None:
    return tika_result.text


def load_text_from_text_lazy(text_lazy: LazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = memview.tobytes().decode(errors=settings.decode_error_handler)
        return text


@app.task(bind=True, base=FileIndexingTask)
def create_embedding_task(
    self: FileIndexingTask,
    text_lazy: LazyBytes | None,
    file: File,
):
    if text_lazy is None:
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.llm_embedding_text_chunk_size,
        chunk_overlap=settings.llm_embedding_text_chunk_overlap,
    )

    text = load_text_from_text_lazy(text_lazy=text_lazy)

    text_fragments = text_splitter.split_text(text)
    chain(
        chord(
            [
                embed_text.s(fragment)
                for fragment in text_fragments
                if is_natural_language(fragment)
            ],
            persist_embeddings.s(file),
        ),
        complete_async_branch(self),
    ).delay().forget()


class LLMError(Exception):
    pass


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=CREATE_EMBEDDING_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def embed_text(text: str) -> LazyBytes:
    client = get_ollama_client()
    try:
        response = client.embed(
            model=settings.llm_model_embedding,
            input=text,
            options=Options(
                temperature=settings.llm_embedding_temperature,
            ),
        )
    except HTTPError as ex:
        raise LLMError() from ex
    embedding = Embedding(
        text=text,
        vector=list(response.embeddings[0]),
    )

    embedding_bytes = to_json(embedding)
    embedding_bytes_lazy = get_lazybytes_service().from_bytes(embedding_bytes)

    return embedding_bytes_lazy


@persisting_task(
    app,
    IndexingPersister,
)
def persist_embeddings(
    persister: IndexingPersister,
    embeddings_bytes_lazy: list[LazyBytes],
):
    embeddings: list[Embedding] = []
    for embedding_bytes_lazy in embeddings_bytes_lazy:
        with get_lazybytes_service().load_memoryview(embedding_bytes_lazy) as memview:
            embedding: Embedding = from_json(memview.tobytes())
            embeddings.append(embedding)

    persister.set_embeddings(embeddings)
