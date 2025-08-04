import logging
from datetime import datetime

import numpy as np
from common.dependencies import get_queues_service
from common.services.queues_service import QueuesService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression

from api.models.queues_model import OverallQueuesStats

router = APIRouter()

default_queues_service = Depends(get_queues_service)

SAMPLE_PERIODS__S = [
    # 8 hours
    60 * 60 * 8,
    # 4 hours
    60 * 60 * 4,
    # 1 hour
    60 * 60,
    # 30 minutes
    60 * 30,
    # 15 minutes
    60 * 15,
    # 5 minutes
    60 * 5,
]

MIN_R_SQ = 0.5


logger = logging.getLogger(__name__)


@router.get("/")
def get_overall_queue_stats(
    queues_service: QueuesService = default_queues_service,
) -> OverallQueuesStats:
    messages_in_queues = get_message_count(queues_service=queues_service)
    complete_estimate_timestamp = get_completed_estimate(queues_service=queues_service)
    return OverallQueuesStats(
        messages_in_queues=messages_in_queues,
        complete_estimate_timestamp=(
            complete_estimate_timestamp.estimate_timestamp
            if complete_estimate_timestamp is not None
            else None
        ),
    )


@router.get("/{queue_name}/message_count")
def get_message_count(
    queue_name: str | None = None,
    queues_service: QueuesService = default_queues_service,
) -> int:
    message_count = queues_service.get_message_count(queue_name=queue_name)
    return message_count


class CompleteEstimate(BaseModel):
    samples_count: int
    samples_period__s: int
    estimate_timestamp: int


def get_completed_estimate_for_period(
    sample_period__s: int,
    queue_name: str | None = None,
    queues_service: QueuesService = default_queues_service,
) -> CompleteEstimate | None:
    now = datetime.now()

    # fetch samples
    samples_sorted = queues_service.get_queue_samples(
        sample_period__s=sample_period__s, queue_name=queue_name
    )

    # only consider consider if we have enough samples
    if len(samples_sorted) < 2:
        return None

    # only consider samples if they don't contain an idle period
    if any(value <= 0 for _, value in samples_sorted):
        return None

    timestamps = np.array(list(s[0] for s in samples_sorted)).reshape((-1, 1))
    values = np.array(list(s[1] for s in samples_sorted))
    model = LinearRegression().fit(timestamps, values)
    r_sq = model.score(timestamps, values)
    intercept = model.intercept_
    slope = model.coef_

    # only consider models that fit the data reasonably well
    logger.debug("period: %s, , r_sq: %s", sample_period__s, r_sq)
    if r_sq < MIN_R_SQ:
        return None

    # positive slope -> we won't have a time estimate in the future
    if slope >= 0:
        return None

    # solve for y = 0 -> estimate
    estimate_timestamp = -intercept / slope

    # estimate should be in the future
    if estimate_timestamp <= now.timestamp():
        return None

    return CompleteEstimate(
        samples_count=len(samples_sorted),
        samples_period__s=sample_period__s,
        estimate_timestamp=int(estimate_timestamp.item()),
    )


@router.get("/{queue_name}/complete_estimate")
def get_completed_estimate(
    queue_name: str | None = None,
    queues_service: QueuesService = default_queues_service,
) -> CompleteEstimate | None:
    # make complete estimates for different sample periods
    for sample_period__s in SAMPLE_PERIODS__S:
        complete_estimate = get_completed_estimate_for_period(
            sample_period__s=sample_period__s,
            queue_name=queue_name,
            queues_service=queues_service,
        )
        if complete_estimate is not None:
            return complete_estimate
    return None
