import asyncio
import signal
import threading
from datetime import timedelta

import aio_pika
import asyncpg
from pydantic import AmqpDsn, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from commons.outbox.worker.fetcher import PostgresFetcher
from commons.outbox.worker.publisher import RabbitmqPublisher
from commons.outbox.worker.worker import Worker


class Config(BaseSettings):
    prefetch_size: int = 20
    job_id: str = "job"
    postgres_dsn: PostgresDsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    rabbitmq_dsn: AmqpDsn = "amqp://rabbitmq:rabbitmq@localhost:5672/"
    table_name: str = "outbox_test_direct"
    process_timeout: timedelta = timedelta(minutes=1)

    model_config = SettingsConfigDict(env_prefix="OUTBOX_")


async def main() -> None:
    config = Config()  # pyright: ignore[reportCallIssue]

    pool = await asyncpg.create_pool(
        dsn=config.postgres_dsn.encoded_string(),
        min_size=1,
        max_size=10,
    )

    fetcher = PostgresFetcher(
        pool=pool,
        outbox_table_name=config.table_name,
        job_id=f"{config.job_id}-thread-{threading.current_thread().name}",
        process_timeout=config.process_timeout,
    )

    connection = await aio_pika.connect_robust(url=config.rabbitmq_dsn.encoded_string())
    publisher = RabbitmqPublisher(connection)

    worker = Worker(fetcher, publisher)

    signal.signal(signal.SIGTERM, lambda _1, _2: worker.stop())

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
