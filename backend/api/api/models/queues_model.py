from pydantic import BaseModel


class QueuesStats(BaseModel):
    messages_in_queues: int
    paused_queues: list[str]
