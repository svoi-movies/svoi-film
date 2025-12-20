import asyncio

from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from moderator.container import create_container


async def main() -> None:
    container = create_container()
    broker = await container.get(RabbitBroker)

    app = FastStream(broker)
    setup_dishka(container=container, app=app, auto_inject=True)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
