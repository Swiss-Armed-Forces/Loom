# pylint: disable=duplicate-code
import logging

from celery import chain, chord, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_llm_embedding_client,
)
from common.file.file_repository import Embedding, File
from common.services.lazybytes_service import TempLazyBytes, TempTypedLazyBytes
from common.utils.cache import cache
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import APIError

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.tasks.auto_tag_file import signature as auto_tag_file_signature
from worker.settings import settings
from worker.utils.natural_language_detection import is_natural_language
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

CREATE_EMBEDDING_MAX_RETRIES = 15


def signature(file: File) -> Signature:
    """Create the signature for vectorization."""
    if settings.skip_embedding_while_indexing:
        return noop.s()

    return chain(
        create_embedding_task.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


def load_text_from_text_lazy(text_lazy: TempLazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = memview.tobytes().decode(errors=settings.decode_error_handler)
        return text


@app.task(bind=True, base=FileIndexingTask)
def create_embedding_task(
    self: FileIndexingTask,
    text_lazy: TempLazyBytes | None,
    file: File,
):
    if text_lazy is None:
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.llm.embedding.text_chunk_size,
        chunk_overlap=settings.llm.embedding.text_chunk_overlap,
    )

    text = load_text_from_text_lazy(text_lazy=text_lazy)

    text_fragments = text_splitter.split_text(text)

    return self.replace(
        chord(
            [
                embed_text.s(fragment)
                for fragment in text_fragments
                if is_natural_language(fragment)
            ],
            group(
                persist_embeddings.s(file.id_),
                auto_tag_file_signature(file),
            ),
        )
    )


class LLMError(Exception):
    pass


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=CREATE_EMBEDDING_MAX_RETRIES,
    retry_backoff=True,
)
@cache()
def embed_text(text: str) -> TempTypedLazyBytes[Embedding]:
    client = get_llm_embedding_client()
    try:
        response = client.embeddings.create(
            model=settings.llm.embedding.model,
            input=f"{settings.llm.embedding.document_prefix}{text}",
        )
    except APIError as ex:
        raise LLMError() from ex

    embedding = Embedding(
        text=text,
        vector=list(response.data[0].embedding),
    )

    return get_lazybytes_service().from_object(embedding)


@persisting_task(
    app,
    IndexingPersister,
)
def persist_embeddings(
    persister: IndexingPersister,
    embeddings_lazy: list[TempTypedLazyBytes[Embedding]],
):
    embeddings = [
        get_lazybytes_service().load_object(embedding_lazy)
        for embedding_lazy in embeddings_lazy
    ]

    persister.set_embeddings(embeddings)
