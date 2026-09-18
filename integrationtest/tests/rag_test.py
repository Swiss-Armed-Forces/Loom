from pathlib import Path
from uuid import uuid4

import pytest
from common.dependencies import get_celery_app, get_lazybytes_service
from worker.ai.tasks.rag_tool import (
    RankedSearchEmbedding,
    ScoredSearchEmbedding,
    generate_hypothetical_document,
    rerank,
    synthesize_rag_answer_task,
)

from utils.consts import ASSETS_DIR

GET_TIMEOUT = 720

AUTO_TAG_FOLDER = Path("auto_tag_files")


@pytest.mark.flaky(reruns=3)
def test_generate_hypothetical_document():
    result = (
        get_celery_app()
        .send_task(
            generate_hypothetical_document.name,
            args=[
                "What is 1+1 ?",
            ],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert result is not None


def test_rerank():

    filename = "no_tag.txt"

    with open(str(ASSETS_DIR / AUTO_TAG_FOLDER / filename), "rb") as f:
        text = f.read()

    text_lazy = get_lazybytes_service().from_bytes(text)

    data = ScoredSearchEmbedding(
        file_id=uuid4(),
        file_score=0,
        text_score=0,
        text_lazy=text_lazy,
    )

    question = "Why is the sky blue ?"

    result = (
        get_celery_app()
        .send_task(
            rerank.name,
            args=[data, question],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert result is not None


def test_synthesize_rag_answer():
    filename = "no_tag.txt"

    with open(str(ASSETS_DIR / AUTO_TAG_FOLDER / filename), "rb") as f:
        text = f.read()

    text_lazy = get_lazybytes_service().from_bytes(text)

    data = [
        RankedSearchEmbedding(
            file_id=uuid4(),
            file_score=0,
            text_score=0,
            text_lazy=text_lazy,
            rank=1,
        )
    ]

    question = "Why is the sky blue ?"

    result = (
        get_celery_app()
        .send_task(
            synthesize_rag_answer_task.name,
            args=[data, question],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert result is not None
    assert len(result.answer) > 0
