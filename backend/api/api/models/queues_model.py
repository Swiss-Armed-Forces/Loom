from pydantic import BaseModel


class OverallQueuesStats(BaseModel):
    messages_in_queues: int
    complete_estimate_timestamp: int | None
