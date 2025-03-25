import logging
from contextlib import asynccontextmanager
from random import choices
from string import ascii_letters
from typing import AsyncGenerator

from redis import StrictRedis
from redis.asyncio import StrictRedis as StrictRedisAsync

from common.messages.messages import (
    MessageSubscribConfirmation,
    MessageSubscribe,
    MessageUnsubscribe,
    MessageUnsubscribeConfirmation,
    PubSubMessage,
)

logger = logging.getLogger(__name__)

PUBSUB_META_CHANNEL_NAME_LENGTH: int = 30


class InvalidMessageException(Exception):
    pass


class _PubSubAsync:

    def __init__(self, redis_client_async: StrictRedisAsync):
        self._redis_client_async = redis_client_async
        self._pubsub_client = self._redis_client_async.pubsub()

        self._pubsub_client_meta_channel_name = "".join(
            choices(ascii_letters, k=PUBSUB_META_CHANNEL_NAME_LENGTH)
        )

    @classmethod
    async def create(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        await self._pubsub_client.subscribe(self._pubsub_client_meta_channel_name)
        return self

    async def close(self):
        await self._pubsub_client.close()

    async def publish_message(self, message: PubSubMessage) -> int:
        """Publish ``message`` Returns the number of subscribers the message was
        delivered to."""
        # deliver messages on the meta channel by default
        message_channel = (
            message.channel
            if message.channel is not None
            else self._pubsub_client_meta_channel_name
        )
        return await self._redis_client_async.publish(
            message_channel, message.model_dump_json()
        )

    async def subscribe(self, channels: set[str]):
        receivers = await self.publish_message(
            PubSubMessage(
                channel=self._pubsub_client_meta_channel_name,
                message=MessageSubscribe(channels=channels),
            ),
        )
        assert receivers == 1

    async def _do_subscribe(self, message: MessageSubscribe):
        if len(message.channels) <= 0:
            return
        await self._pubsub_client.subscribe(*message.channels)
        receivers = await self.publish_message(
            PubSubMessage(
                message=MessageSubscribConfirmation(channels=message.channels),
            ),
        )
        assert receivers == 1

    async def unsubscribe(self, channels: set[str]):
        receivers = await self.publish_message(
            PubSubMessage(
                channel=self._pubsub_client_meta_channel_name,
                message=MessageUnsubscribe(channels=channels),
            ),
        )
        assert receivers == 1

    async def _do_unsubscribe(self, message: MessageUnsubscribe):
        if len(message.channels) <= 0:
            return
        await self._pubsub_client.unsubscribe(*message.channels)
        receivers = await self.publish_message(
            PubSubMessage(
                message=MessageUnsubscribeConfirmation(channels=message.channels),
            ),
        )
        assert receivers == 1

    async def _handle_subscription_messages(self, message: PubSubMessage) -> bool:
        inner_message = message.message
        if isinstance(inner_message, MessageSubscribe):
            await self._do_subscribe(inner_message)
            return True
        if isinstance(inner_message, MessageUnsubscribe):
            await self._do_unsubscribe(inner_message)
            return True
        return False

    async def get_message(self) -> PubSubMessage:

        # read message
        while True:
            pubsub_message = await self._pubsub_client.get_message(
                ignore_subscribe_messages=True,
                # Passing timeout=None to wait indefinitely in accordance with the API docs
                timeout=None,  # type: ignore
            )

            if pubsub_message is None:
                continue

            # decode message
            message_data = pubsub_message["data"]
            try:
                message = PubSubMessage.model_validate_json(
                    message_data,
                )
            except ValueError as ex:
                logger.error("Unexpected message: %s", pubsub_message, exc_info=ex)
                continue

            handled = await self._handle_subscription_messages(message)
            if handled:
                continue

            return message


class PubSubService:
    def __init__(self, redis_client: StrictRedis, redis_client_async: StrictRedisAsync):
        self._redis_client = redis_client
        self._redis_client_async = redis_client_async

    @asynccontextmanager
    async def open_async(self) -> AsyncGenerator[_PubSubAsync, None]:
        pubsub = await _PubSubAsync.create(
            self._redis_client_async,
        )
        try:
            yield pubsub
        finally:
            await pubsub.close()

    def publish_message(self, message: PubSubMessage) -> int:
        """Publish ``message`` Returns the number of subscribers the message was
        delivered to."""
        # deliver messages on the meta channel by default
        if message.channel is None:
            raise InvalidMessageException("message.channel can not be None")
        return self._redis_client.publish(message.channel, message.model_dump_json())
