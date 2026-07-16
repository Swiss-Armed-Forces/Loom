from datetime import datetime

from pydantic import BaseModel, Field, RootModel


class DeadTask(Exception):
    """Exception raised when a task comes from a dead letter queue."""


class XDeathEntry(BaseModel):
    queue: str
    reason: str
    count: int
    exchange: str
    routing_keys: list[str] = Field(alias="routing-keys")
    # AMQP 0.9.1:
    time: datetime | None = None
    # AMQP 1.0:
    first_time: datetime | None = Field(alias="first-time", default=None)
    last_time: datetime | None = Field(alias="last-time", default=None)


class XDeathHeader(RootModel[list[XDeathEntry]]):
    def __getitem__(self, item) -> XDeathEntry:
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)
