from dataclasses import dataclass
from uuid import UUID

from aio_pika import Message
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

from .worker import Publisher


@dataclass
class MessageForPublish:
    id: UUID
    routing_key: str
    message: str


class RabbitmqPublisher(Publisher):

    def __init__(self, connection: AbstractRobustConnection) -> None:
        self.__connection = connection
        self.__channel = self.__connection.channel()
        self.__exchanges: dict[str, AbstractExchange] = {}

    async def _get_exchange(self, topic: str) -> AbstractExchange:
        try:
            return self.__exchanges[topic]
        except KeyError:
            return await self.__channel.get_exchange(name=topic, ensure=True)

    async def publish(self, topic: str, message: MessageForPublish) -> None:
        exchange = await self._get_exchange(topic)
        await exchange.publish(
            message=Message(body=message.message.encode("utf-8")),
            routing_key=message.routing_key,
        )
