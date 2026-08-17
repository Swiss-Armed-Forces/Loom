from typing import Literal, Union

from pydantic import BaseModel, Field


class MessageNoop(BaseModel):
    type: Literal["noop"] = "noop"


class MessageSubscribe(BaseModel):
    type: Literal["subscribe"] = "subscribe"
    channels: set[str] = set()


class MessageSubscribeConfirmation(BaseModel):
    type: Literal["subscribeConfirmation"] = "subscribeConfirmation"
    channels: set[str] = set()


class MessageUnsubscribe(BaseModel):
    type: Literal["unsubscribe"] = "unsubscribe"
    channels: set[str] = set()


class MessageUnsubscribeConfirmation(BaseModel):
    type: Literal["unsubscribeConfirmation"] = "unsubscribeConfirmation"
    channels: set[str] = set()


class MessageError(BaseModel):
    type: Literal["error"] = "error"
    message: str


class MessageFileUpdate(BaseModel):
    type: Literal["fileUpdate"] = "fileUpdate"
    fileId: str


class MessageFileSave(BaseModel):
    type: Literal["fileSave"] = "fileSave"
    fileId: str


class MessageQueryIdExpired(BaseModel):
    type: Literal["queryIdExpired"] = "queryIdExpired"
    old_id: str
    new_id: str


class PubSubMessage(BaseModel):
    channel: str | None = (
        None  # None means the message will be delivered on the meta channel
    )

    message: Union[
        MessageNoop,
        MessageSubscribe,
        MessageSubscribeConfirmation,
        MessageUnsubscribe,
        MessageUnsubscribeConfirmation,
        MessageFileUpdate,
        MessageFileSave,
        MessageQueryIdExpired,
        MessageError,
    ] = Field(discriminator="type")
