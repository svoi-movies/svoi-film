from datetime import datetime
from typing import Any, ClassVar, Protocol
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from commons.outbox.worker.worker import MessageStatus


class Encoder[T: Any](Protocol):

    def encode(self, object: T) -> str: ...


def use_outbox(
    metadata: sa.MetaData,
    table_name: str = "outbox",
    schema: str | None = None,
) -> sa.Table:
    return sa.Table(
        table_name,
        metadata,
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("status", sa.Enum(MessageStatus), nullable=False),
        sa.Column("destination_topic", sa.String(64), nullable=False),
        sa.Column("routing_key", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("tries", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("process_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("process_done_at", sa.DateTime(timezone=True), nullable=True),
        schema=schema,
    )


class OutboxRepository:
    table: ClassVar[sa.Table]

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.__session = session

    async def add(
        self,
        message_id: UUID,
        destination_topic: str,
        routing_key: str,
        message: str,
        created_at: datetime,
    ) -> None:
        # TODO: Actually session.execute flushes session, not really sure that it is ok
        await self.__session.execute(
            sa.insert(self.table).values(
                {
                    "id": message_id,
                    "job_id": None,
                    "status": MessageStatus.PENDING,
                    "destination_topic": destination_topic,
                    "routing_key": routing_key,
                    "message": message,
                    "tries": 0,
                    "created_at": created_at,
                    "process_started_at": None,
                    "process_done_at": None,
                }
            )
        )
