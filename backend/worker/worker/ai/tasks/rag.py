import logging
import re
from typing import Generator, Sequence
from uuid import UUID, uuid4

from celery import chain, chord, group
from celery.canvas import Signature
from common.ai_context.ai_context_repository import AiContext
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
    get_llm_chat_client,
    get_llm_embedding_client,
    get_llm_hyde_client,
    get_llm_rerank_client,
    get_pubsub_service,
)
from common.messages.messages import (
    MessageChatBotAnswerComplete,
    MessageChatBotCitation,
    MessageChatBotToken,
    PubSubMessage,
)
from common.services.lazybytes_service import TempLazyBytes, TempTypedLazyBytes
from common.services.query_builder import QueryParameters
from numpy import array, mean
from openai import APIError
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, computed_field

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.settings import settings
from worker.utils.clustering import kde_filter_highest_cluster

logger = logging.getLogger(__name__)

app = get_celery_app()

MAX_FILES_KNN_SEARCH = 7

MAX_TEXT_LENGTH = int(2 * (1024**2))  # 2 MiB

MAX_SCORED_SEARCH_EMBEDDINGS_FOR_RERANKING = 50

RERANK_MIN_RANK = 0
RERANK_RANK_RANGE = 5
RERANK_MAX_RANK = RERANK_MIN_RANK + RERANK_RANK_RANGE
RERANK_THRESHOLD = RERANK_MIN_RANK + RERANK_RANK_RANGE * 0.6
SCORED_RANK_SCALING_FACTOR = 10

MAX_RANKED_SEARCH_EMBEDDINGS = 10

LLM_MAX_TOKENS_RAG = 100

RAG_MAX_RETRIES = 15


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
    rank: float

    @computed_field  # type: ignore[misc]
    @property
    def scored_rank(self) -> float:
        return (
            self.file_score * self.text_score * self.rank * SCORED_RANK_SCALING_FACTOR
        )


def load_text_from_text_lazy(text_lazy: TempLazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_TEXT_LENGTH]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        return text


def signature(context: AiContext, question: str) -> Signature:
    return chain(
        chord(
            [
                embed_question.s(question),
                group(
                    # HyDE: Hypothetical Document Embeddings
                    # Generate multiple hypothetical documents that could answer the question
                    # This helps improve retrieval by creating diverse query representation.
                    chain(
                        generate_hypothetical_document.s(question),
                        embed_document.s(),
                    )
                    for _ in range(settings.llm.hyde.num_documents)
                ),
            ],
            aggregate_embeddings.s(),
        ),
        fetch_scored_search_embeddings.s(context.query),
        sort_and_limit_scored_search_embeddings.s(),
        rerank_scored_search_embeddings.s(context, question),
    )


class LLMError(Exception):
    pass


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def embed_question(question: str) -> TempTypedLazyBytes[Sequence[float]]:
    """Embed a single question."""
    client = get_llm_embedding_client()
    try:
        response = client.embeddings.create(
            model=settings.llm.embedding.model,
            input=[f"{settings.llm.embedding.query_prefix}{question}"],
        )
    except APIError as ex:
        raise LLMError("Document embedding failed") from ex

    embedding = response.data[0].embedding
    logger.debug("Embedded question into %d-dim vector", len(embedding))
    return get_lazybytes_service().from_object(embedding)


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def generate_hypothetical_document(question: str) -> str:
    """Generate a single hypothetical document."""
    prompt = f"""Given the question below, write a short factual passage that would
directly answer it. Do not explain or preface your answer. Just write the passage
as if it were from a document. Keep your answer in a paragraph of
{settings.llm.embedding.text_chunk_size} tokens or less.

Question: {question}

Passage:"""
    client = get_llm_hyde_client()
    messages = [
        ChatCompletionUserMessageParam(role="user", content=prompt),
    ]

    try:
        response = client.chat.completions.create(
            model=settings.llm.hyde.model,
            messages=messages,
            temperature=settings.llm.hyde.temperature,
            extra_headers=settings.llm.hyde.extra_headers,
            extra_body=settings.llm.hyde.extra_body,
        )
    except APIError as ex:
        raise LLMError("Hypothetical document generation failed") from ex

    doc = settings.llm.hyde.truncate_response(
        (response.choices[0].message.content or "").strip()
    )

    logger.debug("Hypothetical generated document: %.100s...", doc)
    return doc


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def embed_document(document: str) -> TempTypedLazyBytes[Sequence[float]]:
    """Embed a single document."""
    client = get_llm_embedding_client()
    try:
        response = client.embeddings.create(
            model=settings.llm.embedding.model,
            input=[f"{settings.llm.embedding.document_prefix}{document}"],
        )
    except APIError as ex:
        raise LLMError("Document embedding failed") from ex

    embedding = response.data[0].embedding
    logger.debug("Embedded document into %d-dim vector", len(embedding))
    return get_lazybytes_service().from_object(embedding)


@app.task(base=AiContextProcessingTask)
def aggregate_embeddings(
    lazy_embeddings_generated: tuple[
        TempTypedLazyBytes[Sequence[float]], list[TempTypedLazyBytes[Sequence[float]]]
    ],
) -> TempTypedLazyBytes[Sequence[float]]:
    """Aggregate embeddings by computing their mean."""
    lazy_embedding_question, lazy_embeddings_hyde = lazy_embeddings_generated
    embeddings = [
        get_lazybytes_service().load_object(lazy_embedding)
        for lazy_embedding in [lazy_embedding_question] + lazy_embeddings_hyde
    ]
    embeddings_array = array(embeddings)
    mean_embedding: list[float] = mean(embeddings_array, axis=0).tolist()

    logger.info(
        "Aggregated %d embeddings into %d-dim vector",
        len(embeddings),
        len(mean_embedding),
    )

    return get_lazybytes_service().from_object(mean_embedding)


@app.task(base=AiContextProcessingTask)
def fetch_scored_search_embeddings(
    embedding_lazy: TempTypedLazyBytes[Sequence[float]], query: QueryParameters
) -> list[ScoredSearchEmbedding]:
    embedding = get_lazybytes_service().load_object(embedding_lazy)

    scored_search_embeddings = []
    for knn_search_embedding in get_file_repository().get_embedding_generator_by_knn(
        query=query, embedding_vectors=[embedding], k=MAX_FILES_KNN_SEARCH
    ):
        text_lazy = get_lazybytes_service().from_bytes(
            knn_search_embedding.text.encode()
        )
        scored_search_embeddings.append(
            ScoredSearchEmbedding(
                file_id=knn_search_embedding.file_id,
                file_score=knn_search_embedding.file_score,
                text_score=knn_search_embedding.text_score,
                text_lazy=text_lazy,
            )
        )
    return scored_search_embeddings


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


@app.task(bind=True, base=AiContextProcessingTask)
def rerank_scored_search_embeddings(
    self: AiContextProcessingTask,
    scored_search_embeddings: list[ScoredSearchEmbedding],
    context: AiContext,
    question: str,
):
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
                chatbot_query.s(context, question),
            ),
        )
    )


def _invoke_rerank_llm(
    prompt: str,
) -> float:
    client = get_llm_rerank_client()
    messages = [
        ChatCompletionUserMessageParam(role="user", content=prompt),
    ]

    try:
        response = client.chat.completions.create(
            model=settings.llm.rerank.model,
            messages=messages,
            temperature=settings.llm.rerank.temperature,
            extra_headers=settings.llm.rerank.extra_headers,
            extra_body=settings.llm.rerank.extra_body,
        )
    except APIError as ex:
        raise LLMError() from ex

    # search and extract rank
    rank_search = re.search(
        r"^\s*(?P<rank>[0-9.]+)", response.choices[0].message.content or ""
    )
    rank = float(
        rank_search.group("rank") if rank_search is not None else RERANK_MIN_RANK
    )

    # enforce bounds
    if rank < RERANK_MIN_RANK:
        return RERANK_MIN_RANK
    if rank > RERANK_MAX_RANK:
        return RERANK_MAX_RANK

    return rank


def send_rerank_chatbot_query(text: str, question: str) -> float:
    rerank_prompt = f"""PROMPT: Rank the relevance of the TEXT based in the context
of the QUESTION on a scale from {RERANK_MIN_RANK} to {RERANK_MAX_RANK}.

Where the rankings mean the following:

0: The TEXT is completely unrelevant to the QUESTION.
1: The TEXT is unrelevant to the QUESTION.
2: The TEXT is little relevant to the QUESTION.
3: The TEXT is somewhat relevant to the QUESTION.
4: The TEXT is relevant to the QUESTION.
5: The TEXT is extremely relevant to the QUESTION.

Do NOT use any previous knowledge.
Only answer with one number and no additional text.
--------------------
TEXT: {text}
--------------------
QUESTION: {question}
--------------------
RANK:"""

    rank = _invoke_rerank_llm(rerank_prompt)
    return rank


@app.task(
    base=AiContextProcessingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def rerank(
    scored_search_embedding: ScoredSearchEmbedding,
    question: str,
) -> RankedSearchEmbedding:
    text = load_text_from_text_lazy(scored_search_embedding.text_lazy)
    rank = send_rerank_chatbot_query(
        text,
        question,
    )

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


def _stream_chat_llm(
    messages: Sequence[ChatCompletionMessageParam],
) -> Generator[str, None, None]:
    client = get_llm_chat_client()
    all_messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system", content=settings.llm_chat_system_prompt
        ),
        *messages,
    ]

    try:
        stream = client.chat.completions.create(
            model=settings.llm.chat.model,
            messages=all_messages,
            stream=True,
            temperature=settings.llm.chat.temperature,
            extra_headers=settings.llm.chat.extra_headers,
            extra_body=settings.llm.chat.extra_body,
        )
    except APIError as ex:
        raise LLMError() from ex
    for token in stream:
        message_content = token.choices[0].delta.content
        if message_content is None:
            continue
        yield message_content


# pylint: disable=too-many-locals
@app.task(
    base=AiContextProcessingTask,
    autoretry_for=tuple([LLMError]),
    max_retries=RAG_MAX_RETRIES,
    retry_backoff=True,
)
def chatbot_query(
    sorted_ranked_search_embeddings: list[RankedSearchEmbedding],
    context: AiContext,
    question: str,
):

    # build answer_context
    answer_context = ""
    for sorted_ranked_search_embedding in reversed(sorted_ranked_search_embeddings):
        text = load_text_from_text_lazy(sorted_ranked_search_embedding.text_lazy)
        answer_context += f"* {text}\n"

    messages: list[ChatCompletionMessageParam]
    if len(sorted_ranked_search_embeddings) > 0:
        task_prompt = f"""TASK: Your task is to answer the human's QUESTION
using the CONTEXT below.

Do NOT use any previous knowledge which is not contained in the CONTEXT.

Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.
Keep your answer concise and brief.
Always answer in the following language: {settings.translate_target}
--------------------
CONTEXT: {answer_context}"""
        messages = [
            ChatCompletionUserMessageParam(role="user", content=task_prompt),
            ChatCompletionUserMessageParam(
                role="user", content=f"QUESTION: {question}"
            ),
        ]

    else:
        task_prompt = f"""TASK: Tell the user that they should refine their QUERY
or QUESTION because you could not find enough information in the data to answer their QUESTION.

Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.
Keep your answer concise and brief."""
        messages = [
            ChatCompletionUserMessageParam(role="user", content=task_prompt),
        ]

    # send all the tokens to the pubsub channel
    answer = ""
    for message_content in _stream_chat_llm(messages=messages):
        answer += message_content
        receivers = get_pubsub_service().publish_message(
            PubSubMessage(
                channel=str(context.id_),
                message=MessageChatBotToken(token_id=uuid4(), token=message_content),
            )
        )
        if receivers < 1:
            # nobody is actually listening: abort
            logger.info("No receiver for llm token")
            return

    for sorted_ranked_search_embedding in sorted_ranked_search_embeddings:
        text = load_text_from_text_lazy(sorted_ranked_search_embedding.text_lazy)
        rank = round(sorted_ranked_search_embedding.scored_rank, 2)
        receivers = get_pubsub_service().publish_message(
            PubSubMessage(
                channel=str(context.id_),
                message=MessageChatBotCitation(
                    id=uuid4(),
                    file_id=sorted_ranked_search_embedding.file_id,
                    text=text,
                    rank=rank,
                ),
            )
        )
        if receivers < 1:
            # nobody is actually listening: abort
            logger.info("No receiver for citations")
            return

    receivers = get_pubsub_service().publish_message(
        PubSubMessage(
            channel=str(context.id_),
            message=MessageChatBotAnswerComplete(),
        )
    )

    logger.debug(
        "Question: %s, Answer: %s, Citations: %s",
        question,
        answer,
        set(str(f.file_id) for f in sorted_ranked_search_embeddings),
    )
