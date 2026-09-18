from random import shuffle
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest
from ai.llm_error_stubs import length_finish_reason_error
from common.dependencies import (
    get_llm_embedding_client,
    get_llm_hyde_agent,
    get_llm_rag_rerank_agent,
)
from common.services.lazybytes_service import InMemoryTempLazyBytesService, LazyBytes
from openai import APIConnectionError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.tasks.rag_tool import (
    RERANK_MAX_RANK,
    RERANK_MIN_RANK,
    LLMError,
    RankedSearchEmbedding,
    ScoredSearchEmbedding,
    _RerankResult,
    aggregate_embeddings,
    apply_rerank_threshold,
    embed_document,
    embed_question,
    filter_ranked_search_embeddings,
    generate_hypothetical_document,
    rerank,
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


@pytest.fixture
def embedding_client() -> MagicMock:
    """The embedding client, mocked and pre-set with a concrete vector."""
    client = cast(MagicMock, get_llm_embedding_client())
    client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=EMBEDDING)]
    )
    return client


@pytest.fixture
def rerank_agent() -> MagicMock:
    """The rerank LLM agent, mocked and pre-set with a top-of-scale rank."""
    agent = cast(MagicMock, get_llm_rag_rerank_agent())
    agent.run_sync.return_value = _agent_result(_RerankResult(rank=RERANK_MAX_RANK))
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
    """Regression guard for #287, applied to the HyDE fanout.

    ``generate_hypothetical_document`` is a chord member, and a chord aborts as soon as
    one member raises -- which would discard the question embedding and every sibling
    document, leaving the question unanswered.
    """
    hyde_agent.run_sync.side_effect = error

    assert generate_hypothetical_document(_final_attempt(), QUESTION) is None


def test_generate_hypothetical_document_drops_empty_passage(hyde_agent: MagicMock):
    hyde_agent.run_sync.return_value = _agent_result("   ")

    assert generate_hypothetical_document(_first_attempt(), QUESTION) is None


def test_embed_document_skips_dropped_document(embedding_client: MagicMock):
    """A dropped hypothetical document must not reach the embedding model."""
    assert embed_document(_first_attempt(), None) is None
    embedding_client.embeddings.create.assert_not_called()


def test_embed_document_drops_document_when_exhausted(embedding_client: MagicMock):
    embedding_client.embeddings.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "http://embedding-llm")
    )

    assert embed_document(_final_attempt(), "a passage") is None


def test_embed_question_never_degrades(embedding_client: MagicMock):
    """Without the question embedding there is nothing to search: fail the chord."""
    embedding_client.embeddings.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "http://embedding-llm")
    )

    with pytest.raises(LLMError):
        embed_question(QUESTION)


def test_aggregate_embeddings_skips_dropped_documents(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """Dropped HyDE members must not skew -- or abort -- the aggregated mean."""
    question_embedding = lazybytes_service_inmemory.from_object([1.0, 1.0, 1.0])
    hyde_embedding = lazybytes_service_inmemory.from_object([3.0, 3.0, 3.0])

    aggregated = aggregate_embeddings((question_embedding, [hyde_embedding, None]))

    assert lazybytes_service_inmemory.load_object(aggregated) == [2.0, 2.0, 2.0]


def test_aggregate_embeddings_survives_every_document_dropped(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    question_embedding = lazybytes_service_inmemory.from_object([1.0, 2.0, 3.0])

    aggregated = aggregate_embeddings((question_embedding, [None, None]))

    assert lazybytes_service_inmemory.load_object(aggregated) == [1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# rerank -- the same chord-member shape, with the same #287 blind spot
# ---------------------------------------------------------------------------


def test_rerank_returns_rank(rerank_agent: MagicMock):
    ranked = rerank(_first_attempt(), _scored_search_embedding(), QUESTION)

    assert ranked.rank == RERANK_MAX_RANK
    rerank_agent.run_sync.assert_called_once()


def test_rerank_retries_while_budget_remains(rerank_agent: MagicMock):
    rerank_agent.run_sync.side_effect = length_finish_reason_error()

    with pytest.raises(LLMError):
        rerank(_first_attempt(), _scored_search_embedding(), QUESTION)


def test_rerank_drops_chunk_when_exhausted(rerank_agent: MagicMock):
    """A chunk that cannot be ranked is dropped, not fatal to its siblings.

    ``LengthFinishReasonError`` is the #287 failure, and the rerank chord used to abort
    outright on it instead of dropping the one chunk that could not be ranked.
    """
    rerank_agent.run_sync.side_effect = length_finish_reason_error()

    ranked = rerank(_final_attempt(), _scored_search_embedding(), QUESTION)

    assert ranked.rank == RERANK_MIN_RANK
    assert apply_rerank_threshold([ranked]) == []
