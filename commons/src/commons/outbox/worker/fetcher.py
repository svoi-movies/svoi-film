from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncGenerator, cast

import asyncpg

from ..entity import Message, MessageStatus
from .worker import Fetcher


class PostgresFetcher(Fetcher):

    def __init__(
        self,
        pool: asyncpg.Pool,
        outbox_table_name: str,
        job_id: str,
        process_timeout: timedelta,
        max_retries: int,
    ) -> None:
        self._pool = pool
        self._outbox_table_name = outbox_table_name
        self._job_id = job_id
        self._timeout = process_timeout
        self._max_retries = max_retries

    @asynccontextmanager
    async def transactional(
        self, isolation_level: str
    ) -> AsyncGenerator[asyncpg.Connection]:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            tx = connection.transaction(isolation=isolation_level)  # type: ignore
            async with tx:
                yield connection

    async def fetch_messages_batch(self) -> list[Message]:
        async with self.transactional("repeatable_read") as connection:
            messages = await self._select_messages_batch(connection)
            if not messages:
                return []
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
            await self._mark_messages_sent_tx(connection, messages)

    async def _select_messages_batch(
        self,
        conn: asyncpg.Connection,
    ) -> list[Message]:
        q = f"""
            SELECT 
                id, 
                job_id, 
                status, 
                destination_topic,
                message, 
                tries, 
                created_at, 
                process_started_at,
                process_done_at,
                process_timeout_ms,
                rowversion,
                routing_key
            FROM {self._outbox_table_name}
            WHERE
                status = '{MessageStatus.PENDING}'
                OR (
                    status = '{MessageStatus.IN_PROGRESS}' 
                    AND tries < {self._max_retries} 
                    AND now() - process_started_at >= (process_timeout_ms || ' milliseconds')::interval
                )
            LIMIT 20
            FOR UPDATE
            SKIP LOCKED
            """
        records: list[asyncpg.Record] = await conn.fetch(
            q,
        )
        return [Message(**dict(r)) for r in records]

    def _build_msg_ids(self, messages: list[Message]) -> str:
        return ", ".join([f"'{m.id}'" for m in messages])

    async def _mark_messages_processing_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = self._build_msg_ids(messages)
        q = f"""
            UPDATE {self._outbox_table_name}
            SET
                tries = tries + 1,
                process_started_at = now(), 
                status = '{MessageStatus.IN_PROGRESS}',
                job_id = $1,
                process_timeout_ms = $2
            WHERE 
                id IN ({msg_ids})
            """
        await conn.execute(
            q,
            self._job_id,
            int(self._timeout.total_seconds() * 1000),
        )

    async def _mark_messages_sent_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = self._build_msg_ids(messages)

        clauses = [
            f"(id = '{msg.id}' AND rowversion = {msg.rowversion})" for msg in messages
        ]

        clause = "OR ".join(clauses)
        await conn.execute(
            f"""
            UPDATE {self._outbox_table_name}
            SET
                process_done_at = now(), 
                rowversion = rowversion + 1,
                status = '{MessageStatus.SENT}'
            WHERE 
                id IN ({msg_ids})
                AND ({clause})
            """,
        )

    async def _mark_messages_for_retry_tx(
        self,
        conn: asyncpg.Connection,
        messages: list[Message],
    ) -> None:
        msg_ids = self._build_msg_ids(messages)
        await conn.execute(
            f"""
            UPDATE {self._outbox_table_name}
            SET
                job_id = NULL,
                status = '{MessageStatus.PENDING}',
                rowversion = rowversion + 1,
            WHERE 
                id IN ({msg_ids})
            """
        )
