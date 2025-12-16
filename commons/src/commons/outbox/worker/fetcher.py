from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncGenerator, cast

import asyncpg
from asyncpg.transaction import Transaction

from .worker import Fetcher, Message, MessageStatus


class PostgresFetcher(Fetcher):

    def __init__(
        self,
        pool: asyncpg.Pool,
        outbox_table_name: str,
        job_id: str,
        process_timeout: timedelta,
    ) -> None:
        self._pool = pool
        self._outbox_table_name = outbox_table_name
        self._job_id = job_id
        self._timeout = process_timeout

    @asynccontextmanager
    async def transactional(
        self, isolation_level: str
    ) -> AsyncGenerator[asyncpg.Connection]:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            async with connection.transaction(isolation=isolation_level) as tx:  # type: ignore
                tx = cast(Transaction, tx)
                yield connection
                await tx.commit()

    async def fetch_messages_batch(self) -> list[Message]:
        async with self.transactional("repeatable_read") as connection:
            messages = await self._select_messages_batch(connection)
            await self._mark_messages_processing_tx(connection, messages)
            return messages

    async def mark_messages_for_retry(self, messages: list[Message]) -> None:
        if not messages:
            return
        async with self.transactional("repeatable_read") as connection:
            await self._mark_messages_for_retry_tx(connection, messages)

    async def mark_messages_sent(self, messages: list[Message]) -> None:
        if not messages:
            return
        async with self.transactional("repeatable_read") as connection:
            await self._mark_messages_for_retry_tx(connection, messages)

    async def _select_messages_batch(
        self,
        conn: asyncpg.Connection,
    ) -> list[Message]:
        records: list[asyncpg.Record] = await conn.fetchmany(
            f"""
            SELECT 
                id, 
                job_id, 
                status, 
                destination_topic,
                message, 
                tries, 
                created_at, 
                process_started_at, 
                process_done_at
            FROM {self._outbox_table_name}
            WHERE
                status = '{MessageStatus.PENDING}'
            LIMIT {self.max}
            FOR UPDATE
            SKIP LOCKE
            """,
            args=(),
        )
        return [Message.model_validate(r) for r in records]

    async def _mark_messages_processing_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = [m.id for m in messages]
        await conn.execute(
            f"""
            UPDATE {self._outbox_table_name}
            SET
                tries = tries + 1,
                process_started_at = now(), 
                rowversion = roweversion + 1
                job_id = $1,
                process_timeout = $2
            WHERE 
                id IN ($3)
            """,
            self._job_id,
            self._timeout,
            msg_ids,
        )

    async def _mark_messages_sent_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = [m.id for m in messages]
        await conn.execute(
            f"""
            UPDATE {self._outbox_table_name}
            SET
                process_done_at = now(), 
                status = {MessageStatus.SENT}
            WHERE 
                id IN ($2)
            """,
            self._job_id,
            msg_ids,
        )

    async def _mark_messages_for_retry_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = [m.id for m in messages]
        await conn.execute(
            f"""
            UPDATE {self._outbox_table_name}
            SET
                max_processing_time = NULL,
                job_id = NULL,
                status = {MessageStatus.PENDING}
            WHERE 
                id IN ($2)
            """,
            self._job_id,
            msg_ids,
        )
