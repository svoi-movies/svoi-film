import asyncio
import logging
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
    job_id: str = "outbox"
    postgres_dsn: PostgresDsn
    rabbitmq_dsn: AmqpDsn
    table_name: str = "outbox"
    process_timeout: timedelta = timedelta(minutes=1)
    max_retries: int = 5

    model_config = SettingsConfigDict(env_prefix="OUTBOX_")


async def main() -> None:
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    config = Config()  # pyright: ignore[reportCallIssue]
    logging.info(f"Started outbox worker with table={config.table_name}")

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
        max_retries=config.max_retries,
    )

    connection = await aio_pika.connect_robust(url=config.rabbitmq_dsn.encoded_string())
    publisher = RabbitmqPublisher(connection)
    worker = Worker(fetcher, publisher)

    signal.signal(signal.SIGTERM, lambda _1, _2: worker.stop())

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
