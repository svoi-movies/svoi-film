import json
from typing import Any

import aio_pika
from aio_pika.abc import AbstractConnection


class EventPublisher:
    def __init__(self, connection: AbstractConnection) -> None:
        self._connection = connection

    async def publish(self, routing_key: str, event: dict[str, Any]) -> None:
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange("streaming", durable=True)

        await exchange.publish(
            message=aio_pika.Message(
                body=json.dumps(event).encode(),
                content_type="application/json",
            ),
            routing_key=routing_key,
        )
