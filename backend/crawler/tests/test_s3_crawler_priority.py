"""`_deduce_priority`: a hint that must never be able to fail an ingest."""

from unittest.mock import MagicMock

import pytest
from common.llm.return_types import IndexingUrgency
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from common.services.task_scheduling_service import IndexingPriority
from minio import Minio
from pydantic_ai.exceptions import ModelHTTPError

from crawler.s3_crawler import S3Crawler

# pylint: disable=protected-access


def _crawler(agent: MagicMock) -> S3Crawler:
    return S3Crawler(
        s3_client=MagicMock(spec=Minio),
        bucket_name="loom-intake",
        bucket_alias=None,
        file_storage_service=InMemoryFileStorageLazyBytesService(threshold_bytes=64),
        task_scheduling_service=MagicMock(),
        index_prioritization_agent=agent,
    )


def _agent_answering(urgency: IndexingUrgency) -> MagicMock:
    agent = MagicMock()
    agent.run_sync.return_value = MagicMock(output=urgency)
    return agent


@pytest.mark.parametrize(
    "urgency, priority",
    [
        (IndexingUrgency.LOW, IndexingPriority.LOW),
        (IndexingUrgency.MEDIUM, IndexingPriority.MEDIUM),
        (IndexingUrgency.HIGH, IndexingPriority.HIGH),
    ],
)
def test_every_rubric_level_maps_to_a_broker_priority(
    urgency: IndexingUrgency, priority: IndexingPriority
):
    """The rubric runs 0..2 and the broker's values are 0/4/5, so the two cannot be the
    same enum and a level with no mapping would be a KeyError per object."""
    assert _crawler(_agent_answering(urgency))._deduce_priority(
        "//stick/a.eml", 1024
    ) is (priority)


def test_a_failing_decision_model_does_not_fail_the_object():
    """`_download_object` raising means the object is never recorded, so the next poll
    offers it again and re-stores its whole body -- forever."""
    agent = MagicMock()
    agent.run_sync.side_effect = RuntimeError("ollama is not there")

    assert _crawler(agent)._deduce_priority("//stick/a.eml", 1024) is (
        IndexingPriority.MEDIUM
    )


def test_a_permanent_failure_is_only_paid_for_once():
    """A misconfigured model reproduces on every object, and a mirrored stick is
    hundreds of thousands of them."""
    agent = MagicMock()
    agent.run_sync.side_effect = ModelHTTPError(status_code=404, model_name="typo")
    crawler = _crawler(agent)

    for _ in range(3):
        assert (
            crawler._deduce_priority("//stick/a.eml", 1024) is IndexingPriority.MEDIUM
        )

    assert agent.run_sync.call_count == 1


def test_a_transient_failure_is_asked_again():
    """An inference service that is restarting answers the next object."""
    agent = MagicMock()
    agent.run_sync.side_effect = ModelHTTPError(status_code=503, model_name="tev1")
    crawler = _crawler(agent)

    for _ in range(3):
        assert (
            crawler._deduce_priority("//stick/a.eml", 1024) is IndexingPriority.MEDIUM
        )

    assert agent.run_sync.call_count == 3
