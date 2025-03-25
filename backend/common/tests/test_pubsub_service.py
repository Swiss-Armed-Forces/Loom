from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.client import PubSub

from common.dependencies import get_redis_client, get_redis_client_async
from common.messages.messages import (
    MessageNoop,
    MessageSubscribConfirmation,
    MessageSubscribe,
    MessageUnsubscribe,
    MessageUnsubscribeConfirmation,
    PubSubMessage,
)
from common.messages.pubsub_service import (
    InvalidMessageException,
    PubSubService,
    _PubSubAsync,
)


def test_publish_message_sync():
    redis_client = get_redis_client()
    redis_client_async = get_redis_client_async()

    pubsub_service = PubSubService(
        redis_client=redis_client, redis_client_async=redis_client_async
    )

    message = PubSubMessage(channel="a channel", message=MessageNoop())
    pubsub_service.publish_message(message)

    redis_client.publish.assert_called_once_with(
        message.channel, message.model_dump_json()
    )


def test_publish_message_sync_raises_on_none_channel():
    redis_client = get_redis_client()
    redis_client_async = get_redis_client_async()

    pubsub_service = PubSubService(
        redis_client=redis_client, redis_client_async=redis_client_async
    )

    message = PubSubMessage(channel=None, message=MessageNoop())
    with pytest.raises(InvalidMessageException):
        pubsub_service.publish_message(message)


@pytest.mark.asyncio
async def test_open_async():
    redis_client = get_redis_client()

    redis_pubsub_client = AsyncMock(spec=PubSub)
    redis_pubsub_client.get_message = AsyncMock()
    redis_pubsub_client.subscribe = AsyncMock()
    redis_pubsub_client.close = AsyncMock()

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client

    pubsub_service = PubSubService(
        redis_client=redis_client, redis_client_async=redis_client_async
    )

    async with pubsub_service.open_async() as _:
        pass

    redis_pubsub_client.subscribe.assert_called_once()
    redis_pubsub_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_publish_message_async():
    redis_pubsub_client = MagicMock(spec=PubSub)

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client
    redis_client_async.publish = AsyncMock()

    async_pubsub_service = _PubSubAsync(redis_client_async=redis_client_async)

    message = PubSubMessage(channel="a channel", message=MessageNoop())

    await async_pubsub_service.publish_message(message=message)

    redis_client_async.publish.assert_called_once_with(
        message.channel, message.model_dump_json()
    )


@pytest.mark.asyncio
async def test_publish_message_async_uses_meta_channel():

    redis_pubsub_client = MagicMock(spec=PubSub)

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client
    redis_client_async.publish = AsyncMock()

    async_pubsub_service = _PubSubAsync(redis_client_async=redis_client_async)
    meta_channel_name = (
        # pylint: disable=protected-access
        async_pubsub_service._pubsub_client_meta_channel_name
    )

    message = PubSubMessage(channel=None, message=MessageNoop())

    await async_pubsub_service.publish_message(message=message)

    redis_client_async.publish.assert_called_once_with(
        meta_channel_name,
        message.model_dump_json(),
    )


@pytest.mark.asyncio
async def test_get_message():
    expected_message = PubSubMessage(channel=None, message=MessageNoop())

    redis_pubsub_client = MagicMock(spec=PubSub)
    redis_pubsub_client.get_message = AsyncMock()
    redis_pubsub_client.get_message.return_value = {
        "data": expected_message.model_dump_json()
    }

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client

    async_pubsub_service = _PubSubAsync(redis_client_async=redis_client_async)

    message = await async_pubsub_service.get_message()

    assert message == expected_message


class EndOfTestException(Exception):
    pass


@pytest.mark.asyncio
async def test_get_message_handle_subscription():
    expected_channels = set(["a channel"])
    expected_message = PubSubMessage(
        channel=None, message=MessageSubscribe(channels=expected_channels)
    )

    get_messge_calls = 0

    async def get_message(*_, **__):
        nonlocal get_messge_calls
        get_messge_calls += 1
        if get_messge_calls == 1:
            return {"data": expected_message.model_dump_json()}
        raise EndOfTestException()

    redis_pubsub_client = AsyncMock(spec=PubSub)
    redis_pubsub_client.get_message = AsyncMock()
    redis_pubsub_client.get_message.side_effect = get_message
    redis_pubsub_client.subscribe = AsyncMock()

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client
    redis_client_async.publish = AsyncMock()
    redis_client_async.publish.return_value = 1  # = receivers

    async_pubsub_service = _PubSubAsync(redis_client_async=redis_client_async)
    meta_channel_name = (
        # pylint: disable=protected-access
        async_pubsub_service._pubsub_client_meta_channel_name
    )

    with pytest.raises(EndOfTestException):
        await async_pubsub_service.get_message()

    redis_pubsub_client.subscribe.assert_called_once_with(*expected_channels)
    redis_client_async.publish.assert_called_once_with(
        meta_channel_name,
        PubSubMessage(
            message=MessageSubscribConfirmation(channels=expected_channels),
        ).model_dump_json(),
    )


@pytest.mark.asyncio
async def test_get_message_handle_unsubscription():
    expected_channels = set(["a channel"])
    expected_message = PubSubMessage(
        channel=None, message=MessageUnsubscribe(channels=expected_channels)
    )

    get_messge_calls = 0

    async def get_message(*_, **__):
        nonlocal get_messge_calls
        get_messge_calls += 1
        if get_messge_calls == 1:
            return {"data": expected_message.model_dump_json()}
        raise EndOfTestException()

    redis_pubsub_client = AsyncMock(spec=PubSub)
    redis_pubsub_client.get_message = AsyncMock()
    redis_pubsub_client.get_message.side_effect = get_message
    redis_pubsub_client.unsubscribe = AsyncMock()

    redis_client_async = get_redis_client_async()
    redis_client_async.pubsub.return_value = redis_pubsub_client
    redis_client_async.publish = AsyncMock()
    redis_client_async.publish.return_value = 1  # = receivers

    async_pubsub_service = _PubSubAsync(redis_client_async=redis_client_async)
    meta_channel_name = (
        # pylint: disable=protected-access
        async_pubsub_service._pubsub_client_meta_channel_name
    )

    with pytest.raises(EndOfTestException):
        await async_pubsub_service.get_message()

    redis_pubsub_client.unsubscribe.assert_called_once_with(*expected_channels)
    redis_client_async.publish.assert_called_once_with(
        meta_channel_name,
        PubSubMessage(
            message=MessageUnsubscribeConfirmation(channels=expected_channels),
        ).model_dump_json(),
    )
