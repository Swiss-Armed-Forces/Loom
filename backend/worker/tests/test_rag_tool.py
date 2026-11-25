from random import shuffle
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import httpx
import pytest
from ai.llm_error_stubs import length_finish_reason_error
from common.ai_context.tool_models import RagSearchResult
from common.dependencies import get_file_repository
from common.file.file_repository import File, FilePurePath, KnnSearchEmbedding
from common.llm.exceptions import LLMError
from common.llm.return_types import Relevance, RerankResult
from common.services.lazybytes_service import InMemoryTempLazyBytesService, LazyBytes
from openai import APIConnectionError
from pydantic_ai.embeddings.result import EmbeddingResult, EmbedInputType
from pydantic_ai.exceptions import ModelAPIError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.tasks.rag_tool import (
    NO_MATCHING_FILES_ANSWER,
    HydeVariant,
    RankedSearchEmbedding,
    ScoredSearchEmbedding,
    aggregate_embeddings,
    apply_rerank_threshold,
    embed_document,
    embed_question,
    fetch_scored_search_embeddings,
    filter_ranked_search_embeddings,
    generate_hypothetical_document,
    rag_pipeline_task,
    rerank,
)
from worker.dependencies import (
    get_llm_embedder,
    get_llm_hyde_agent,
    get_llm_rag_rerank_so_agent,
)

# pylint: disable=redefined-outer-name

QUESTION = "who signed the contract?"

EMBEDDING = [0.5, 0.5, 0.5]


def _agent_result(output: object) -> SimpleNamespace:
    """Build a minimal stand-in for an ``Agent.run_sync`` result."""
    return SimpleNamespace(output=output)


def _bound_task(*, is_last_attempt: bool) -> AiContextProcessingTask:
    """Stand in for the ``self`` of a bound task.

    ``mock_init`` replaces ``celery_app.task`` with a no-op decorator, so under test the
    task bodies are plain functions and ``self`` has to be passed in explicitly.
    ``BaseTask.is_last_attempt`` derives from the live retry state, which only exists
    inside a worker; it is covered by ``common/tests/test_base_task.py``.
    """
    task = MagicMock(spec=AiContextProcessingTask)
    task.is_last_attempt = is_last_attempt
    return cast(AiContextProcessingTask, task)


def _first_attempt() -> AiContextProcessingTask:
    return _bound_task(is_last_attempt=False)


def _final_attempt() -> AiContextProcessingTask:
    """A task whose whole retry budget has already been spent."""
    return _bound_task(is_last_attempt=True)


@pytest.fixture
def hyde_agent() -> MagicMock:
    """The HyDE LLM agent, mocked and pre-set with a successful response."""
    agent = cast(MagicMock, get_llm_hyde_agent())
    agent.run_sync.return_value = _agent_result("a passage")
    return agent


def _embedding_result(input_type: EmbedInputType) -> EmbeddingResult:
    return EmbeddingResult(
        embeddings=[EMBEDDING],
        inputs=["irrelevant"],
        input_type=input_type,
        model_name="test-embedding",
        provider_name="test",
    )


@pytest.fixture
def embedder() -> MagicMock:
    """The embedder, mocked and pre-set with a concrete vector."""
    embedder = cast(MagicMock, get_llm_embedder())
    embedder.embed_query_sync.return_value = _embedding_result("query")
    embedder.embed_documents_sync.return_value = _embedding_result("document")
    return embedder


@pytest.fixture
def file_repository() -> MagicMock:
    """The file repository, mocked by ``mock_init`` and returned for stubbing."""
    return cast(MagicMock, get_file_repository())


def _knn_embedding(file_id: UUID, text: str, text_score: float) -> KnnSearchEmbedding:
    return KnnSearchEmbedding(
        file_id=file_id,
        file=File(
            full_name=FilePurePath("/irrelevant.txt"),
            source="test",
            sha256="0" * 64,
            size=1,
        ),
        file_score=1.0,
        text_score=text_score,
        text=text,
    )


@pytest.fixture
def rerank_agent() -> MagicMock:
    """The rerank LLM agent, mocked and pre-set with a top-of-scale rank."""
    agent = cast(MagicMock, get_llm_rag_rerank_so_agent())
    agent.run_sync.return_value = _agent_result(
        RerankResult(rank=Relevance.VERY_RELEVANT)
    )
    return agent


def _scored_search_embedding() -> ScoredSearchEmbedding:
    return ScoredSearchEmbedding(
        file_id=uuid4(),
        file_score=1.0,
        text_score=1.0,
        text_lazy=LazyBytes(embedded_data=b"some chunk text"),
    )


@pytest.mark.parametrize(
    "clusters",
    [
        [[1.0, 1.0, 1.0], [3.0, 3.0], [5.0, 5.0, 5.0]],
        [[1.0, 1.0, 1.0, 1.0, 1.0], [5.0]],
        [[1.0, 1.0, 1.0, 1.0, 1.0]],
        [[1.0]],
    ],
)
def test_filter_ranked_file_text(clusters: list[list[float]]):
    def get_ranked_search_embedding(rank: float):
        return RankedSearchEmbedding(
            file_id=uuid4(),
            file_score=1,
            text_score=1,
            text_lazy=LazyBytes(embedded_data=b""),
            rank=rank,
        )

    shuffled_ranked_search_embedding: list[RankedSearchEmbedding] = []
    for cluster in clusters:
        last_cluster_ranked_search_embedding: list[RankedSearchEmbedding] = []
        for rank in cluster:
            ranked_search_embedding = get_ranked_search_embedding(rank)
            shuffled_ranked_search_embedding.append(ranked_search_embedding)
            last_cluster_ranked_search_embedding.append(ranked_search_embedding)

    # repeat for different input orderings
    for _ in range(len(shuffled_ranked_search_embedding)):
        shuffle(shuffled_ranked_search_embedding)

        filtered_ranks = filter_ranked_search_embeddings(
            shuffled_ranked_search_embedding
        )

        assert len(filtered_ranks) == len(last_cluster_ranked_search_embedding)
        for c in last_cluster_ranked_search_embedding:
            assert c in filtered_ranks


# ---------------------------------------------------------------------------
# HyDE group -- a failing hypothetical document must not abort the chord
# ---------------------------------------------------------------------------


def test_generate_hypothetical_document_returns_passage(hyde_agent: MagicMock):
    assert generate_hypothetical_document(_first_attempt(), QUESTION) == "a passage"
    hyde_agent.run_sync.assert_called_once()


def test_generate_hypothetical_document_retries_while_budget_remains(
    hyde_agent: MagicMock,
):
    """Transient failures must still be retried rather than silently dropped."""
    hyde_agent.run_sync.side_effect = APIConnectionError(
        request=httpx.Request("POST", "http://hyde-llm")
    )

    with pytest.raises(LLMError):
        generate_hypothetical_document(_first_attempt(), QUESTION)


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(length_finish_reason_error(), id="length-limit-reached"),
        pytest.param(
            APIConnectionError(request=httpx.Request("POST", "http://hyde-llm")),
            id="connection-error",
        ),
    ],
)
def test_generate_hypothetical_document_drops_document_when_exhausted(
    hyde_agent: MagicMock, error: Exception
):
    """A document that cannot be generated is dropped, not fatal to the fanout.

    ``generate_hypothetical_document`` is a chord member, and a chord aborts as soon as
    one member raises -- which would discard the question embedding and every sibling
    document, leaving the question unanswered.
    """
    hyde_agent.run_sync.side_effect = error

    assert generate_hypothetical_document(_final_attempt(), QUESTION) is None


def test_generate_hypothetical_document_drops_empty_passage(hyde_agent: MagicMock):
    hyde_agent.run_sync.return_value = _agent_result("   ")

    assert generate_hypothetical_document(_first_attempt(), QUESTION) is None


def test_hyde_variants_reach_the_model_as_distinct_prompts(hyde_agent: MagicMock):
    """Every variant has to change the prompt.

    The group sends one task per variant, so a variant that renders the same prompt as
    another is an LLM call contributing nothing to the fanout.
    """
    prompts = set()
    for variant in HydeVariant:
        generate_hypothetical_document(_first_attempt(), QUESTION, variant)
        prompts.add(hyde_agent.run_sync.call_args.args[0])

    assert len(prompts) == len(list(HydeVariant))
    assert all(QUESTION in prompt for prompt in prompts)


def test_hyde_default_variant_is_plain(hyde_agent: MagicMock):
    """Callers dispatching by name with the question alone must keep working."""
    generate_hypothetical_document(_first_attempt(), QUESTION)
    default_prompt = hyde_agent.run_sync.call_args.args[0]

    generate_hypothetical_document(_first_attempt(), QUESTION, HydeVariant.PLAIN)

    assert hyde_agent.run_sync.call_args.args[0] == default_prompt


def test_hyde_seed_reaches_the_model(hyde_agent: MagicMock):
    """Members sharing a variant are separated by the seed alone.

    ``num_documents`` above the variant count makes the variants repeat, so without a
    distinct seed those members would send an identical request.
    """
    for seed in (0, 1):
        generate_hypothetical_document(
            _first_attempt(), QUESTION, HydeVariant.PLAIN, seed
        )
        assert hyde_agent.run_sync.call_args.kwargs["model_settings"]["seed"] == seed


@pytest.mark.usefixtures("hyde_agent")
def test_hyde_variant_arrives_as_a_plain_string():
    """Celery delivers the variant as the string the enum serialises to."""
    result = generate_hypothetical_document(
        _first_attempt(), QUESTION, cast(HydeVariant, "report")
    )

    assert result == "a passage"


def test_embed_document_skips_dropped_document(embedder: MagicMock):
    """A dropped hypothetical document must not reach the embedding model."""
    assert embed_document(_first_attempt(), None) is None
    embedder.embed_documents_sync.assert_not_called()


def test_embed_document_drops_document_when_exhausted(embedder: MagicMock):
    embedder.embed_documents_sync.side_effect = ModelAPIError(
        "test-embedding", "connection failed"
    )

    assert embed_document(_final_attempt(), "a passage") is None


def test_embed_question_never_degrades(embedder: MagicMock):
    """Without the question embedding there is nothing to search: fail the chord."""
    embedder.embed_query_sync.side_effect = ModelAPIError(
        "test-embedding", "connection failed"
    )

    with pytest.raises(LLMError):
        embed_question(QUESTION)


def test_aggregate_embeddings_searches_with_every_surviving_embedding(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """Every embedding becomes its own probe, and a dropped member contributes none."""
    question_embedding = lazybytes_service_inmemory.from_object([1.0, 1.0, 1.0])
    hyde_embedding = lazybytes_service_inmemory.from_object([3.0, 3.0, 3.0])

    aggregated = aggregate_embeddings((question_embedding, [hyde_embedding, None]))

    assert lazybytes_service_inmemory.load_object(aggregated) == [
        [1.0, 1.0, 1.0],
        [3.0, 3.0, 3.0],
    ]


def test_aggregate_embeddings_survives_every_document_dropped(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """The question embedding alone still searches for the question itself."""
    question_embedding = lazybytes_service_inmemory.from_object([1.0, 2.0, 3.0])

    aggregated = aggregate_embeddings((question_embedding, [None, None]))

    assert lazybytes_service_inmemory.load_object(aggregated) == [[1.0, 2.0, 3.0]]


def test_fetch_scored_search_embeddings_reaches_each_chunk_once(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    file_repository: MagicMock,
):
    """A chunk several probes reach is reranked once, at its best score.

    Every embedding is searched with as its own kNN clause, so Elasticsearch returns the
    chunks near each of them and the overlap arrives as repeats of one chunk.
    """
    file_id = uuid4()
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.get_embedding_generator_by_knn.return_value = iter(
        [
            _knn_embedding(file_id, "shared chunk", text_score=0.2),
            _knn_embedding(file_id, "shared chunk", text_score=0.9),
            _knn_embedding(file_id, "other chunk", text_score=0.4),
        ]
    )
    embeddings = lazybytes_service_inmemory.from_object([[1.0], [2.0]])

    scored = fetch_scored_search_embeddings(embeddings, "*")

    assert sorted(s.text_score for s in scored) == [0.4, 0.9]
    assert file_repository.get_embedding_generator_by_knn.call_args.kwargs[
        "embedding_vectors"
    ] == [[1.0], [2.0]]


def test_fetch_scored_search_embeddings_opens_the_snapshot_it_searches(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    file_repository: MagicMock,
):
    """The point-in-time's keep-alive is short and only a search extends it, so it is
    opened by the task that searches rather than carried in from upstream."""
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.get_embedding_generator_by_knn.return_value = iter([])

    fetch_scored_search_embeddings(
        lazybytes_service_inmemory.from_object([[1.0]]), "file_type:pdf"
    )

    file_repository.open_point_in_time.assert_called_once()
    query = file_repository.get_embedding_generator_by_knn.call_args.kwargs["query"]
    assert query.query_id == "pit-id"
    assert query.search_string == "file_type:pdf"


# ---------------------------------------------------------------------------
# rag_pipeline_task
# ---------------------------------------------------------------------------


def test_rag_pipeline_task_answers_a_query_matching_nothing_without_the_pipeline(
    file_repository: MagicMock,
):
    """A query matching no file bounds every kNN clause to nothing, so the stages below
    can only spend an LLM call per probe to arrive at the same empty answer."""
    file_repository.count_by_query.return_value = 0
    task = _first_attempt()

    result = rag_pipeline_task(task, QUESTION, "file_type:nonsense")

    assert result == RagSearchResult(answer=NO_MATCHING_FILES_ANSWER, chunks=[])
    cast(MagicMock, task).replace.assert_not_called()


# ---------------------------------------------------------------------------
# rerank -- the same chord-member shape, with the same failure to guard against
# ---------------------------------------------------------------------------


def test_rerank_returns_rank(rerank_agent: MagicMock):
    ranked = rerank(_first_attempt(), _scored_search_embedding(), QUESTION)

    assert ranked.rank == Relevance.VERY_RELEVANT
    rerank_agent.run_sync.assert_called_once()


def test_rerank_retries_while_budget_remains(rerank_agent: MagicMock):
    rerank_agent.run_sync.side_effect = length_finish_reason_error()

    with pytest.raises(LLMError):
        rerank(_first_attempt(), _scored_search_embedding(), QUESTION)


def test_rerank_drops_chunk_when_exhausted(rerank_agent: MagicMock):
    """A chunk that cannot be ranked is dropped, not fatal to its siblings.

    ``LengthFinishReasonError`` arrives when reasoning tokens exhaust ``max_tokens``,
    and aborting the rerank chord on it discards every chunk that was ranked
    successfully.
    """
    rerank_agent.run_sync.side_effect = length_finish_reason_error()

    ranked = rerank(_final_attempt(), _scored_search_embedding(), QUESTION)

    assert ranked.rank == Relevance.COMPLETELY_IRRELEVANT
    assert apply_rerank_threshold([ranked]) == []


@pytest.mark.parametrize(
    "rank, kept",
    [
        (Relevance.SOMEWHAT_RELEVANT, False),
        (Relevance.RELEVANT, True),
    ],
)
def test_the_rerank_threshold_keeps_relevant_and_above(rank: Relevance, kept: bool):
    """The cut sits between SOMEWHAT_RELEVANT and RELEVANT, and the scale is discrete,
    so nothing in between can land on it."""
    ranked = _scored_search_embedding()
    embedding = RankedSearchEmbedding(
        file_id=ranked.file_id,
        file_score=ranked.file_score,
        text_score=ranked.text_score,
        text_lazy=ranked.text_lazy,
        rank=rank,
    )

    assert apply_rerank_threshold([embedding]) == ([embedding] if kept else [])
