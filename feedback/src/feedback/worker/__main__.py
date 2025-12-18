import asyncio

from aio_pika.abc import AbstractConnection, ExchangeType
from dishka import AsyncContainer
from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from feedback.container import create_container
from feedback.persistence.schema import wire_mappers


async def declare_exchanges(container: AsyncContainer) -> None:
    connection = await container.get(AbstractConnection)
    async with connection.channel() as channel:
        _ = await channel.declare_exchange(
            "ikbo0722.titles", ExchangeType.TOPIC, durable=True
        )


async def main() -> None:
    wire_mappers()
    container = create_container()
    broker = await container.get(RabbitBroker)
    await declare_exchanges(container)

    app = FastStream(broker)
    print(app.broker)

    setup_dishka(container=container, app=app, auto_inject=True)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
