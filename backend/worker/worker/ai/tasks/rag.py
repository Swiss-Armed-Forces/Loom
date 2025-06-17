import logging
import re
from typing import Generator, Sequence
from uuid import UUID, uuid4

import numpy as np
from celery import chain, chord
from celery.canvas import Signature
from common.ai_context.ai_context_repository import AiContext
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
    get_pubsub_service,
)
from common.messages.messages import (
    MessageChatBotCitation,
    MessageChatBotToken,
    PubSubMessage,
)
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from langchain_text_splitters import RecursiveCharacterTextSplitter
from numpy import array, linspace
from ollama import Message, Options
from pydantic import BaseModel, computed_field
from pydantic_core import from_json, to_json
from scipy.signal import argrelextrema
from sklearn.neighbors import KernelDensity

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.dependencies import get_ollama_client
from worker.settings import settings
from worker.utils.async_task_branch import complete_async_branch

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


# Contains the chunks of a files text with a scored the knn score of the .
class ScoredSearchEmbedding(BaseModel):
    file_id: UUID
    file_score: float
    text_score: float
    text_lazy: LazyBytes

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


def load_text_from_text_lazy(text_lazy: LazyBytes) -> str:
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_TEXT_LENGTH]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        return text


def signature(context: AiContext, question: str) -> Signature:
    return chain(
        create_question_embedding.s(question),
        fetch_scored_search_embeddings.s(context.query),
        sort_and_limit_scored_search_embeddings.s(),
        rerank_scored_search_embeddings.s(context, question),
    )


@app.task(base=AiContextProcessingTask)
def create_question_embedding(text: str) -> LazyBytes:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.llm_embedding_text_chunk_size,
        chunk_overlap=settings.llm_embedding_text_chunk_overlap,
    )
    texts = text_splitter.split_text(text)

    client = get_ollama_client()
    response = client.embed(
        model=settings.llm_model_embedding,
        input=texts,
        options=Options(
            temperature=settings.llm_embedding_temperature,
        ),
    )

    embeddings_vectors = response.embeddings
    embedding_vectors_bytes = to_json(embeddings_vectors)
    embedding_vectors_bytes_lazy = get_lazybytes_service().from_bytes(
        embedding_vectors_bytes
    )

    return embedding_vectors_bytes_lazy


@app.task(base=AiContextProcessingTask)
def fetch_scored_search_embeddings(
    embedding_vectors_bytes_lazy: LazyBytes, query: QueryParameters
) -> list[ScoredSearchEmbedding]:
    with get_lazybytes_service().load_memoryview(
        embedding_vectors_bytes_lazy
    ) as memview:
        embedding_vectors: list[list[float]] = from_json(memview.tobytes())

    scored_search_embeddings = []
    for knn_search_embedding in get_file_repository().get_embedding_generator_by_knn(
        query=query, embedding_vectors=embedding_vectors, k=MAX_FILES_KNN_SEARCH
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
    chain(
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
        ),
        complete_async_branch(self),
    ).delay().forget()


def _invoke_rerank_llm(
    prompt: str,
) -> float:
    client = get_ollama_client()
    response = client.generate(
        model=settings.llm_model,
        prompt=prompt,
        system=settings.llm_rerank_system_prompt,
        options=Options(
            temperature=settings.llm_rerank_temperature,
        ),
        think=settings.llm_think,
    )

    # search and extract rank
    rank_search = re.search(r"^\s*(?P<rank>[0-9.]+)", response.response)
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


@app.task(base=AiContextProcessingTask)
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
    # can not operate on less than one sample
    if len(ranked_search_embeddings) < 1:
        return ranked_search_embeddings
    # sort input
    sorted_ranked_search_embeddings = sorted(
        ranked_search_embeddings, key=lambda s: s.scored_rank
    )

    # fit kernel density
    reshaped_sorted_ranked_search_embeddings = array(
        [s.scored_rank for s in sorted_ranked_search_embeddings]
    ).reshape(-1, 1)
    kde = KernelDensity(bandwidth="silverman").fit(
        reshaped_sorted_ranked_search_embeddings
    )

    # we span a linspace from [min, max], which we can then sample
    # to generate the linspace we oversample a bit on purpose
    linspace_samples = linspace(
        sorted_ranked_search_embeddings[0].scored_rank,
        sorted_ranked_search_embeddings[-1].scored_rank,
        len(sorted_ranked_search_embeddings) * 4,  # = oversampling
    ).reshape(-1, 1)
    linspace_samples_ranked = kde.score_samples(linspace_samples)
    minimas = argrelextrema(linspace_samples_ranked, np.less)[0]

    if len(minimas) < 1:
        # no minia found:
        return ranked_search_embeddings

    # Filter all but the ones after the last minima -> last cluster
    last_minima = minimas[-1]
    last_minima_value = linspace_samples[last_minima][0]
    filtered_ranked_search_embeddings = [
        s for s in ranked_search_embeddings if s.scored_rank > last_minima_value
    ]
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
    messages: Sequence[Message],
) -> Generator[str, None, None]:
    client = get_ollama_client()
    messages = [Message(role="system", content=settings.llm_chat_system_prompt)] + list(
        messages
    )
    stream = client.chat(
        model=settings.llm_model,
        messages=messages,
        stream=True,
        options=Options(
            temperature=settings.llm_temperature,
        ),
        think=settings.llm_think,
    )
    for token in stream:
        message_content = token.message.content
        if message_content is None:
            continue
        yield message_content


# pylint: disable=too-many-locals
@app.task(base=AiContextProcessingTask)
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

    if len(sorted_ranked_search_embeddings) > 0:
        messages = [
            Message(
                role="system",
                content=f"""TASK: Your task is to answer the human's QUESTION
using the CONTEXT below.

Do NOT use any previous knowledge which is not contained in the CONTEXT.

Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.
Keep your answer concise and brief.
--------------------
CONTEXT: {answer_context}""",
            ),
            Message(role="user", content=f"""QUESTION: {question}"""),
        ]

    else:
        messages = [
            Message(
                role="system",
                content=f"""TASK: Tell the user that he should refine their QUERY
or QUESTION because you could not find enough information in the data to answer his QUESTION.

Keep your answer in a paragraph of {LLM_MAX_TOKENS_RAG} tokens or less.
Keep your answer concise and brief.""",
            )
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

    logger.debug(
        "Question: %s, Answer: %s, Citations: %s",
        question,
        answer,
        set(str(f.file_id) for f in sorted_ranked_search_embeddings),
    )
