import dataclasses
import json
from datetime import datetime
from typing import Any, ClassVar, Protocol
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import registry

from commons.outbox.entity import Message, MessageStatus


class Serializer[T: Any](Protocol):

    def serialize(self, object: T) -> str: ...


class DataclassSerializer[T: Any]:

    @staticmethod
    def serialize_type(value: Any) -> str:
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"Unsupoorted type {type(value)}")

    def serialize(self, object: T) -> str:
        return json.dumps(dataclasses.asdict(object), default=self.serialize_type)


def create_outbox_table(
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
        sa.Column("process_timeout_ms", sa.Integer(), nullable=True),
        sa.Column("rowversion", sa.Integer(), nullable=True),
        schema=schema,
    )


def map_outbox_table(mapper_registry: registry, outbox_table: sa.Table) -> None:
    mapper_registry.map_imperatively(
        Message,
        outbox_table,
        properties={
            "id": outbox_table.c.id,
            "job_id": outbox_table.c.job_id,
            "status": outbox_table.c.status,
            "destination_topic": outbox_table.c.destination_topic,
            "routing_key": outbox_table.c.routing_key,
            "message": outbox_table.c.message,
            "tries": outbox_table.c.tries,
            "created_at": outbox_table.c.created_at,
            "process_started_at": outbox_table.c.process_started_at,
            "process_done_at": outbox_table.c.process_done_at,
            "process_timeout_ms": outbox_table.c.process_timeout_ms,
            "rowversion": outbox_table.c.rowversion,
        },
    )


class OutboxRepository:
    table: ClassVar[sa.Table]

    def __init__(
        self,
        session: AsyncSession,
        serializer: Serializer,
    ) -> None:
        self.__session = session
        self.__serializer = serializer

    def add(
        self,
        message_id: UUID,
        destination_topic: str,
        routing_key: str,
        message: Any,
        created_at: datetime,
    ) -> None:
        msg = Message(
            id=message_id,
            job_id=None,
            status=MessageStatus.PENDING,
            destination_topic=destination_topic,
            routing_key=routing_key,
            message=self.__serializer.serialize(message),
            tries=0,
            created_at=created_at,
            process_started_at=None,
            process_done_at=None,
            process_timeout_ms=None,
            rowversion=0,
        )
        self.__session.add(msg)
