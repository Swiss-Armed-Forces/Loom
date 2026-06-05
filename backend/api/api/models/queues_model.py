from pydantic import BaseModel


class CompleteEstimate(BaseModel):
    samples_count: int
    samples_period__s: int
    estimate_timestamp: int


class OverallQueuesStats(BaseModel):
    messages_in_queues: int
    complete_estimate_timestamp: int | None
    paused_queues_count: int
