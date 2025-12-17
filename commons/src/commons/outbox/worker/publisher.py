import logging

from aio_pika import Message
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

from .. import entity
from .worker import Publisher

logger = logging.getLogger(__name__)


class RabbitmqPublisher(Publisher):

    def __init__(self, connection: AbstractRobustConnection) -> None:
        self.__connection = connection
        self.__channel = self.__connection.channel()
        self.__exchanges: dict[str, AbstractExchange] = {}

    async def _get_exchange(self, topic: str) -> AbstractExchange:
        if not self.__channel.is_initialized:
            self.__channel = await self.__channel
        try:
            return self.__exchanges[topic]
        except KeyError:
            return await self.__channel.get_exchange(name=topic, ensure=True)

    async def publish(self, message: entity.Message) -> None:
        logger.info(f"Publishing message {message.id}")
        exchange = await self._get_exchange(message.destination_topic)
        await exchange.publish(
            message=Message(body=message.message.encode("utf-8")),
            routing_key=message.routing_key,
        )
