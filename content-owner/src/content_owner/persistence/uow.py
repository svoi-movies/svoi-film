import json
from typing import Any, override

import aio_pika
from aio_pika.abc import AbstractConnection
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession

from content_owner.domain.content_owner import (
    ContentOwnerCreatedEvent,
    ContentOwnerDeletedEvent,
    ContentOwnerPermissionsUpdatedEvent,
)
from content_owner.persistence.content_owner_repository import (
    SqlAlchemyContentOwnerRepository,
)
from content_owner.use_cases import interfaces


class ContentOwnerUnitOfWork(UnitOfWork[Any], interfaces.ContentOwnerUnitOfWork):
    """
    Wraps the SQLAlchemy session and routes domain events to the outbox and RabbitMQ.
    """

    def __init__(
        self,
        session: AsyncSession,
        uuid_provider: UUIDProvider,
        dt_provider: DateTimeProvider,
        amqp_connection: AbstractConnection,
    ) -> None:
        super().__init__(session)
        self._outbox_repository = OutboxRepository(
            session, serializer=DataclassSerializer()
        )
        self._uuid_provider = uuid_provider
        self._dt_provider = dt_provider
        self._content_owners = SqlAlchemyContentOwnerRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def content_owners(self) -> interfaces.ContentOwnerRepository:
        return self._content_owners

    @override
    async def __aenter__(self) -> None:
        await UnitOfWork.__aenter__(self)

    @override
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await UnitOfWork.__aexit__(self, exc_type, exc_val, exc_tb)

    @override
    async def commit(self) -> None:
        await UnitOfWork.commit(self)

    @override
    async def rollback(self) -> None:
        await UnitOfWork.rollback(self)

    @override
    async def handle_domain_events(self, events: list[Any]) -> None:
        channel = await self._amqp_connection.channel()
        exchange = await channel.declare_exchange(
            "content-owner", aio_pika.ExchangeType.TOPIC, durable=True
        )
        try:
            for event in events:
                destination_topic = "content-owner"
                if isinstance(event, ContentOwnerCreatedEvent):
                    routing_key = f"content-owner.{event.content_owner_id}.created"
                    body = {
                        "content_owner_id": str(event.content_owner_id),
                        "user_id": str(event.user_id),
                        "company_id": str(event.company_id),
                        "permissions": list(event.permissions),
                        "created_at": event.created_at.isoformat(),
                    }
                elif isinstance(event, ContentOwnerPermissionsUpdatedEvent):
                    routing_key = (
                        f"content-owner.{event.content_owner_id}.permissions-updated"
                    )
                    body = {
                        "content_owner_id": str(event.content_owner_id),
                        "permissions": list(event.permissions),
                        "updated_at": event.updated_at.isoformat(),
                    }
                elif isinstance(event, ContentOwnerDeletedEvent):
                    routing_key = f"content-owner.{event.content_owner_id}.deleted"
                    body = {
                        "content_owner_id": str(event.content_owner_id),
                        "deleted_at": event.deleted_at.isoformat(),
                    }
                else:
                    raise TypeError(
                        f"Can't handle message of type {type(event)}: {event}"
                    )

                self._outbox_repository.add(
                    message_id=self._uuid_provider.new_v4(),
                    created_at=self._dt_provider.now_utc,
                    destination_topic=destination_topic,
                    routing_key=routing_key,
                    message=event,
                )

                await exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(body).encode(),
                        content_type="application/json",
                    ),
                    routing_key=routing_key,
                )
        finally:
            await channel.close()
