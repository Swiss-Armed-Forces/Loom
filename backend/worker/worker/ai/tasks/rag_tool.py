import logging
from enum import StrEnum
from math import ceil
from typing import NamedTuple, Sequence
from uuid import UUID

from celery import chain, chord, group
from common.ai_context.tool_models import RagChunk, RagSearchResult
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)
from common.file.file_repository import KnnSearchEmbedding
from common.llm.exceptions import (
    LLMError,
    LLMTransientError,
    classify_llm_error,
)
from common.llm.prompt_sanitizer import sanitize_document_text
from common.llm.return_types import Relevance
from common.services.lazybytes_service import TempLazyBytes, TempTypedLazyBytes
from common.services.query_builder import QueryParameters
from minio.error import MinioException
from pydantic import BaseModel, computed_field
from urllib3.exceptions import HTTPError as Urllib3HTTPError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.dependencies import (
    get_llm_embedder,
    get_llm_hyde_agent,
    get_llm_rag_rerank_so_agent,
    get_llm_rag_synthesize_agent,
)
from worker.settings import settings
from worker.utils.clustering import kde_filter_highest_cluster

logger = logging.getLogger(__name__)

app = get_celery_app()

# How many files one probe may reach. Tuned rather than derived: it trades the breadth
# of the corpus considered against the Elasticsearch work of one kNN clause, and how
# many files are worth looking at is a property of the corpus.
FILES_PER_PROBE_KNN_SEARCH = 7

MAX_TEXT_LENGTH = int(2 * (1024**2))  # 2 MiB

MAX_SCORED_SEARCH_EMBEDDINGS_FOR_RERANKING = 20

# The probes are hypothetical documents answering one question, so they are meant to
# land in the same neighbourhood and the chunks they agree on are the ones that survive
# deduplication. Where they agree completely, the reranker chooses among the chunks of
# `FILES_PER_PROBE_KNN_SEARCH` files alone, so taking this many chunks from each keeps
# the budget above reachable rather than nominal.
CHUNKS_PER_FILE_KNN_SEARCH = ceil(
    MAX_SCORED_SEARCH_EMBEDDINGS_FOR_RERANKING / FILES_PER_PROBE_KNN_SEARCH
)

# A chunk reaches the synthesiser from RELEVANT upwards: the filter is `>`, and the
# scale is discrete, so this names the highest grade that is still dropped.
RERANK_THRESHOLD = Relevance.SOMEWHAT_RELEVANT
SCORED_RANK_SCALING_FACTOR = 10

MAX_RANKED_SEARCH_EMBEDDINGS = 10

# Read by the agent that called the tool rather than by the user, and that agent is the
# one that chose the query and can widen it. Saying so beats an empty answer, which
# reads as a pipeline that ran and found nothing.
NO_MATCHING_FILES_ANSWER = (
    "No file matches the query, so there is nothing in the corpus to answer from. "
    "Nothing was searched or read. Ask again with a broader query, or with `*` to "
    "search the whole index."
)

LLM_MAX_TOKENS_RAG = 100

RAG_MAX_RETRIES = 15
# Only the transient half of the LLMError hierarchy - see TIKA_RETRY_EXCEPTIONS.
RAG_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (LLMTransientError,)
# For the tasks that also stream a chunk's text out of object storage before
# prompting. minio calls urlopen bare, so an unreachable store arrives as a
# urllib3 error rather than a MinioException.
RAG_STORAGE_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = RAG_RETRY_EXCEPTIONS + (
    MinioException,
    Urllib3HTTPError,
)


# Contains the chunks of a files text with a scored the knn score of the .
class ScoredSearchEmbedding(BaseModel):
    file_id: UUID
    file_score: float
    text_score: float
    text_lazy: TempLazyBytes

    @computed_field  # type: ignore[misc]
    @property
    def score(self) -> float:
        return self.file_score * self.text_score


# Contains the chunks of a files text with a rank based on the user question and
# the knn score of the file.
class RankedSearchEmbedding(ScoredSearchEmbedding):
    rank: Relevance

    @computed_field  # type: ignore[misc]
    @property
    def scored_rank(self) -> float:
        return (
            self.file_score * self.text_score * self.rank * SCORED_RANK_SCALING_FACTOR
        )


class ChunkKey(NamedTuple):
    """What makes two kNN results the same chunk.

    A chunk is identified by its text within its file: the nested embedding carries no
    id of its own, and the same text in two files is two chunks.
    """

    file_id: UUID
    text: str


def load_text_from_text_lazy(text_lazy: TempLazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_TEXT_LENGTH]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        return text


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=RAG_RETRY_EXCEPTIONS,
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def embed_question(question: str) -> TempTypedLazyBytes[Sequence[float]]:
    """Embed a single question.

    Unlike the HyDE members of the same chord this one must not degrade: without the
    question embedding there is nothing to search for, so failing the chord is the
    honest outcome.
    """
    try:
        result = get_llm_embedder().embed_query_sync(
            f"{settings.llm.embedding.query_prefix}{question}"
        )
    except Exception as ex:  # pylint: disable=broad-exception-caught
        raise classify_llm_error(ex, "Question embedding failed") from ex

    embedding = list(result.embeddings[0])
    logger.debug("Embedded question into %d-dim vector", len(embedding))
    return get_lazybytes_service().from_object(embedding)


class HydeVariant(StrEnum):
    """Which kind of document a hypothetical passage imitates.

    A hypothetical document is a retrieval probe that works by resembling a real
    document in the corpus, so the variants name registers the index holds -- OCR'd
    scans, office documents and mail -- rather than styles of authorship.
    """

    PLAIN = "plain"
    REPORT = "report"
    CORRESPONDENCE = "correspondence"
    REFERENCE = "reference"
    RECORD = "record"


# One instruction per variant, rendered into the skeleton `_build_hyde_prompt` holds.
# Each opens a sentence beginning "Given the question below, ...".
_HYDE_VARIANT_INSTRUCTIONS: dict[HydeVariant, str] = {
    HydeVariant.PLAIN: "write a short factual passage that would directly answer it.",
    HydeVariant.REPORT: (
        "write an excerpt from the findings section of a report that answers it."
    ),
    HydeVariant.CORRESPONDENCE: "write the body of a letter or email that answers it.",
    HydeVariant.REFERENCE: (
        "write an encyclopedic entry about its subject that answers it."
    ),
    HydeVariant.RECORD: (
        "write a labelled record entry that answers it, one field per line."
    ),
}


def _build_hyde_prompt(question: str, variant: HydeVariant) -> str:
    """Render the prompt for one hypothetical document.

    The skeleton carries everything the variants share, so the length limit and the no-
    preface guardrail are stated once.
    """
    return f"""Given the question below, {_HYDE_VARIANT_INSTRUCTIONS[variant]}
Do not explain or preface your answer. Just write the passage
as if it were from a document. Keep your answer in a paragraph of
{settings.llm.embedding.text_chunk_size} tokens or less.

Question: {question}

Passage:"""


@app.task(
    bind=True,
    base=AiContextProcessingTask,
    autoretry_for=RAG_RETRY_EXCEPTIONS,
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def generate_hypothetical_document(
    self: AiContextProcessingTask,
    question: str,
    variant: HydeVariant = HydeVariant.PLAIN,
    seed: int = 0,
) -> str | None:
    """Generate a single hypothetical document, or ``None`` if it has to be dropped.

    This runs as a member of the HyDE group inside the ``rag_pipeline_task`` chord.
    Once the retry budget is spent, raising would abort that chord and lose the
    question embedding and every sibling document along with it, leaving the question
    unanswered -- so drop this document instead and let recall degrade.

    ``seed`` separates members that share a variant, which happens whenever
    ``num_documents`` exceeds the variant count.
    """
    # Celery delivers the member as the plain string it serialises to, so coerce it
    # back: an unknown variant is then a ValueError here rather than a KeyError during
    # rendering.
    variant = HydeVariant(variant)
    prompt = _build_hyde_prompt(question, variant)

    agent = get_llm_hyde_agent()

    try:
        # A per-run setting is merged over the agent's, so this adds the seed and
        # leaves `temperature`, `max_tokens` and `thinking` as configured.
        result_agent = agent.run_sync(prompt, model_settings={"seed": seed})

    except Exception as ex:  # pylint: disable=broad-except
        error = classify_llm_error(ex, "Hypothetical document generation failed")
        if isinstance(error, LLMTransientError) and not self.is_last_attempt:
            raise error from ex
        logger.warning(
            "generate_hypothetical_document: dropping %s document, LLM call failed",
            variant,
            exc_info=True,
        )
        return None

    doc = (result_agent.output or "").strip()
    if not doc:
        logger.warning(
            "generate_hypothetical_document: dropping %s document, "
            "LLM returned no text",
            variant,
        )
        return None

    logger.debug("Hypothetical generated %s document: %.100s...", variant, doc)
    return doc


@app.task(
    bind=True,
    base=AiContextProcessingTask,
    autoretry_for=RAG_RETRY_EXCEPTIONS,
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def embed_document(
    self: AiContextProcessingTask, document: str | None
) -> TempTypedLazyBytes[Sequence[float]] | None:
    """Embed a single hypothetical document, or ``None`` if it has to be dropped.

    ``None`` also arrives from ``generate_hypothetical_document`` when that step was
    dropped; embedding nothing would only add a meaningless probe to the search.
    """
    if not document:
        return None

    try:
        result = get_llm_embedder().embed_documents_sync(
            f"{settings.llm.embedding.document_prefix}{document}"
        )
    except Exception as ex:  # pylint: disable=broad-exception-caught
        error = classify_llm_error(ex, "Document embedding failed")
        if isinstance(error, LLMTransientError) and not self.is_last_attempt:
            raise error from ex
        logger.warning(
            "embed_document: dropping document, embedding failed", exc_info=True
        )
        return None

    embedding = list(result.embeddings[0])
    logger.debug("Embedded document into %d-dim vector", len(embedding))
    return get_lazybytes_service().from_object(embedding)


@app.task(base=AiContextProcessingTask)
def aggregate_embeddings(
    lazy_embeddings_generated: tuple[
        TempTypedLazyBytes[Sequence[float]],
        list[TempTypedLazyBytes[Sequence[float]] | None],
    ],
) -> TempTypedLazyBytes[Sequence[Sequence[float]]]:
    """Collect the embeddings the search runs against, one probe per vector.

    A mean over vectors pointing in different directions is dominated by what they share
    and drifts toward the corpus centroid, matching nothing specific. Each embedding is
    therefore carried through as its own kNN probe, and Elasticsearch unions the hits.

    Dropped HyDE members contribute ``None`` and are skipped. The question embedding is
    always present, so the batch is never empty -- and it stays in the set as a probe in
    its own right, matching documents that answer the question literally.
    """
    lazy_embedding_question, lazy_embeddings_hyde = lazy_embeddings_generated
    dropped = sum(
        1 for lazy_embedding in lazy_embeddings_hyde if lazy_embedding is None
    )
    if dropped:
        logger.warning(
            "aggregate_embeddings: %d of %d hypothetical documents were dropped",
            dropped,
            len(lazy_embeddings_hyde),
        )
    embeddings = [
        get_lazybytes_service().load_object(lazy_embedding)
        for lazy_embedding in [lazy_embedding_question, *lazy_embeddings_hyde]
        if lazy_embedding is not None
    ]

    logger.info("Searching with %d embeddings", len(embeddings))

    return get_lazybytes_service().from_object(embeddings)


@app.task(base=AiContextProcessingTask)
def fetch_scored_search_embeddings(
    embeddings_lazy: TempTypedLazyBytes[Sequence[Sequence[float]]],
    query: str,
) -> list[ScoredSearchEmbedding]:
    """Search with every embedding and return the chunks they reach, each once.

    One kNN clause is issued per embedding, so a chunk close to several of them is
    returned by each of those clauses. Collapsing to the best score per chunk happens
    before the text reaches storage: a duplicate that survives costs one reranking LLM
    call and skews ``kde_filter_highest_cluster``, which reads the score distribution.

    The point-in-time is opened here, where it is first used. Its keep-alive runs from
    the moment it is opened and is extended only by a search against it, and this task
    is the only one that searches: opening it any earlier spends that window on the
    probe-building LLM calls instead.
    """
    query_params = QueryParameters(
        query_id=get_file_repository().open_point_in_time(),
        search_string=query,
    )
    embeddings = get_lazybytes_service().load_object(embeddings_lazy)

    best_by_chunk: dict[ChunkKey, KnnSearchEmbedding] = {}
    for knn_search_embedding in get_file_repository().get_embedding_generator_by_knn(
        query=query_params,
        embedding_vectors=embeddings,
        files_k=FILES_PER_PROBE_KNN_SEARCH,
        chunks_per_file=CHUNKS_PER_FILE_KNN_SEARCH,
    ):
        key = ChunkKey(
            file_id=knn_search_embedding.file_id, text=knn_search_embedding.text
        )
        best = best_by_chunk.get(key)
        if best is None or knn_search_embedding.score > best.score:
            best_by_chunk[key] = knn_search_embedding

    logger.info(
        "Searched with %d embeddings, reaching %d distinct chunks",
        len(embeddings),
        len(best_by_chunk),
    )

    return [
        ScoredSearchEmbedding(
            file_id=knn_search_embedding.file_id,
            file_score=knn_search_embedding.file_score,
            text_score=knn_search_embedding.text_score,
            text_lazy=get_lazybytes_service().from_bytes(
                knn_search_embedding.text.encode()
            ),
        )
        for knn_search_embedding in best_by_chunk.values()
    ]


@app.task(base=AiContextProcessingTask)
def sort_and_limit_scored_search_embeddings(
    scored_search_embeddings: list[ScoredSearchEmbedding],
) -> list[ScoredSearchEmbedding]:
    sorted_scored_search_embeddings = sorted(
        scored_search_embeddings, key=lambda s: s.score, reverse=True
    )
    limited_scored_search_embeddings = sorted_scored_search_embeddings[
        :MAX_SCORED_SEARCH_EMBEDDINGS_FOR_RERANKING
    ]
    return limited_scored_search_embeddings


def send_rerank_chatbot_query(text: str, question: str) -> Relevance:
    sanitized_text = sanitize_document_text(text)

    system_one_agent = get_llm_rag_rerank_so_agent()

    try:
        system_one_return = system_one_agent.run_sync(
            f"Question: {question}. Text: {sanitized_text}"
        )
    except Exception as ex:
        raise classify_llm_error(ex, "Reranking document failed") from ex

    return system_one_return.output.rank


@app.task(
    bind=True,
    base=AiContextProcessingTask,
    autoretry_for=RAG_STORAGE_RETRY_EXCEPTIONS,
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def rerank(
    self: AiContextProcessingTask,
    scored_search_embedding: ScoredSearchEmbedding,
    question: str,
) -> RankedSearchEmbedding:
    """Rank one chunk against the question.

    This runs as a member of the ``rerank_and_synthesize`` chord. Once the retry budget
    is spent, raising would abort that chord and discard every chunk that was ranked
    successfully, so fall back to the minimum rank instead -- which
    ``apply_rerank_threshold`` then filters out.
    """
    text = load_text_from_text_lazy(scored_search_embedding.text_lazy)
    try:
        rank = send_rerank_chatbot_query(
            text,
            question,
        )
    except LLMError as ex:
        if isinstance(ex, LLMTransientError) and not self.is_last_attempt:
            raise
        logger.warning(
            "rerank: dropping chunk of file %s, LLM call failed",
            scored_search_embedding.file_id,
            exc_info=True,
        )
        rank = Relevance.COMPLETELY_IRRELEVANT

    return RankedSearchEmbedding(
        file_id=scored_search_embedding.file_id,
        file_score=scored_search_embedding.file_score,
        text_score=scored_search_embedding.text_score,
        text_lazy=scored_search_embedding.text_lazy,
        rank=rank,
    )


@app.task(base=AiContextProcessingTask)
def apply_rerank_threshold(
    ranked_search_embeddings: list[RankedSearchEmbedding],
) -> list[RankedSearchEmbedding]:
    ranked_search_embeddings = [
        sorted_ranked_search_embedding
        for sorted_ranked_search_embedding in ranked_search_embeddings
        if sorted_ranked_search_embedding.rank > RERANK_THRESHOLD
    ]
    return ranked_search_embeddings


@app.task(base=AiContextProcessingTask)
def filter_ranked_search_embeddings(
    ranked_search_embeddings: list[RankedSearchEmbedding],
) -> list[RankedSearchEmbedding]:
    if len(ranked_search_embeddings) < 1:
        return ranked_search_embeddings

    filtered_ranked_search_embeddings = kde_filter_highest_cluster(
        ranked_search_embeddings, lambda rse: rse.scored_rank
    )

    logging.info(
        "filtering ranked file texts. before: %d after: %d",
        len(ranked_search_embeddings),
        len(filtered_ranked_search_embeddings),
    )

    return filtered_ranked_search_embeddings


@app.task(base=AiContextProcessingTask)
def limit_and_sort_ranked_search_embeddings(
    ranked_search_embeddings: list[RankedSearchEmbedding],
) -> list[RankedSearchEmbedding]:
    sorted_ranked_search_embeddings = sorted(
        ranked_search_embeddings, key=lambda s: s.scored_rank, reverse=True
    )
    limited_ranked_search_embeddings = sorted_ranked_search_embeddings[
        :MAX_RANKED_SEARCH_EMBEDDINGS
    ]
    return limited_ranked_search_embeddings


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=RAG_STORAGE_RETRY_EXCEPTIONS,
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def synthesize_rag_answer_task(
    ranked_embeddings: list[RankedSearchEmbedding], question: str
) -> RagSearchResult:
    """Synthesize a grounded answer from ranked document chunks."""
    chunks = [
        RagChunk(
            file_id=e.file_id,
            text=sanitize_document_text(load_text_from_text_lazy(e.text_lazy)),
        )
        for e in ranked_embeddings
    ]
    answer_context = "".join(
        f"<document>\n{c.text}\n</document>\n" for c in reversed(chunks)
    )

    if ranked_embeddings:
        task_prompt = (
            f"TASK: Your task is to answer the human's QUESTION "
            f"using the CONTEXT below.\n\n"
            f"Do NOT use any previous knowledge which is not contained in the CONTEXT.\n\n"
            f"Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.\n"
            f"Keep your answer concise and brief.\n\n"
            f"CONTEXT:\n{answer_context}\n\n"
            f"QUESTION: {question}"
        )
    else:
        task_prompt = (
            f"TASK: Tell the user that they should refine their QUERY "
            f"or QUESTION because you could not find enough information in the data "
            f"to answer their QUESTION.\n\n"
            f"Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.\n"
            f"Keep your answer concise and brief."
        )

    agent = get_llm_rag_synthesize_agent()

    try:
        result = agent.run_sync(task_prompt)

    except Exception as ex:
        raise classify_llm_error(ex, "Answer synthesis failed") from ex

    answer = (result.output or "").strip()

    return RagSearchResult(answer=answer, chunks=chunks)


@app.task(bind=True, base=AiContextProcessingTask)
def rerank_and_synthesize(
    self: AiContextProcessingTask,
    scored_search_embeddings: list[ScoredSearchEmbedding],
    question: str,
):
    """Rerank scored embeddings then synthesize a string answer (no streaming)."""
    return self.replace(
        chord(
            [
                rerank.s(scored_search_embedding, question)
                for scored_search_embedding in scored_search_embeddings
            ],
            chain(
                apply_rerank_threshold.s(),
                filter_ranked_search_embeddings.s(),
                limit_and_sort_ranked_search_embeddings.s(),
                synthesize_rag_answer_task.s(question),
            ),
        )
    )


@app.task(bind=True, base=AiContextProcessingTask)
def rag_pipeline_task(
    self: AiContextProcessingTask, question: str, query: str
) -> RagSearchResult:
    """Orchestrate the full RAG pipeline and return the synthesized answer.

    Args:
        question: What the answer has to address. Every probe is built from it and
            the synthesiser is given it verbatim.
        query: Lucene query string bounding which files the probes may reach. ``*``
            searches the whole index.
    """
    logger.info(
        "rag_pipeline_task: orchestrating RAG pipeline for question '%s' over '%s'",
        question,
        query,
    )
    # The query bounds every kNN clause, so a query matching no file cannot reach a
    # chunk and the stages below would spend an LLM call per probe to arrive at an
    # empty answer. One count answers that before any of them is dispatched.
    if get_file_repository().count_by_query(QueryParameters(search_string=query)) == 0:
        logger.info("rag_pipeline_task: no file matches '%s', nothing to answer", query)
        return RagSearchResult(answer=NO_MATCHING_FILES_ANSWER, chunks=[])

    # Cycling rather than zipping keeps `num_documents` and the variant list from
    # contradicting each other at any operator-chosen value: above the variant count
    # the variants repeat, below it the prefix starts at PLAIN. The index doubles as
    # the seed, so members sharing a variant still differ, and a repeated run of one
    # question samples the same documents -- which is what makes a before/after
    # measurement of retrieval quality readable.
    variants = list(HydeVariant)
    return self.replace(
        chain(
            chord(
                [
                    embed_question.s(question),
                    group(
                        chain(
                            generate_hypothetical_document.s(
                                question, variants[i % len(variants)], i
                            ),
                            embed_document.s(),
                        )
                        for i in range(settings.llm.rag_hyde.num_documents)
                    ),
                ],
                aggregate_embeddings.s(),
            ),
            fetch_scored_search_embeddings.s(query),
            sort_and_limit_scored_search_embeddings.s(),
            rerank_and_synthesize.s(question),
        )
    )


@app.task(bind=True, base=AiContextProcessingTask)
def rag_search_tool_task(
    self: AiContextProcessingTask,
    question: str,
    query: str,
    _context_id: UUID,
) -> RagSearchResult:
    return self.replace(rag_pipeline_task.s(question, query))
