import asyncio

from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from streaming.container import create_container
from streaming.worker.handlers import broker


async def main() -> None:
    container = create_container()
    rabbit_broker = await container.get(RabbitBroker)

    broker.include_router(rabbit_broker)

    app = FastStream(broker)
    setup_dishka(container=container, app=app, auto_inject=True)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
