from typing import Any
from uuid import uuid4

import pytest
from common.dependencies import get_pubsub_service
from common.messages.messages import (
    MessageNoop,
    MessageSubscribeConfirmation,
    PubSubMessage,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    [MessageNoop()],
)
async def test_pubsub_publish_get(message: Any):
    channel_id = str(uuid4())
    pubsub_message = PubSubMessage(channel=channel_id, message=message)

    pubsub = get_pubsub_service()

    async with pubsub.open_async() as pubsub_async:
        await pubsub_async.subscribe(channels={channel_id})

        subscribe_confirmation = await pubsub_async.get_message()
        assert isinstance(subscribe_confirmation.message, MessageSubscribeConfirmation)
        assert subscribe_confirmation.message.channels == {channel_id}

        await pubsub_async.publish_message(message=pubsub_message)
        received_message = await pubsub_async.get_message()
        assert received_message == pubsub_message
