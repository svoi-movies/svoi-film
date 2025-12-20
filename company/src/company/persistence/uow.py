import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractConnection
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession

from company.domain import (
    CompanyCreatedEvent,
    ContentOwnerAddedEvent,
    ContentOwnerPermissionsUpdatedEvent,
    ContentOwnerRemovedEvent,
)
from company.persistence.company_repository import SqlAlchemyCompanyRepository
from company.persistence.content_owner_repository import (
    SqlAlchemyContentOwnerRepository,
)
from company.use_cases import interfaces


@dataclass(frozen=True, slots=True)
class ContentOwnerCreatedPayload:
    content_owner_id: UUID
    user_id: UUID
    company_id: UUID
    permissions: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ContentOwnerPermissionsUpdatedPayload:
    content_owner_id: UUID
    permissions: tuple[str, ...]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ContentOwnerDeletedPayload:
    content_owner_id: UUID
    deleted_at: datetime


class CompanyUnitOfWork(UnitOfWork[Any], interfaces.CompanyUnitOfWork):
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
        self._companies = SqlAlchemyCompanyRepository(session)
        self._content_owners = SqlAlchemyContentOwnerRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def companies(self) -> interfaces.CompanyRepository:
        return self._companies

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
        try:
            exchanges = {
                "company": await channel.declare_exchange(
                    "company", aio_pika.ExchangeType.TOPIC, durable=True
                ),
                "content-owner": await channel.declare_exchange(
                    "content-owner", aio_pika.ExchangeType.TOPIC, durable=True
                ),
            }
            for event in events:
                publish_targets: list[tuple[str, str, dict[str, Any], Any]] = []
                if isinstance(event, CompanyCreatedEvent):
                    publish_targets.append(
                        (
                            "company",
                            f"company.{event.company_id}.created",
                            {
                                "company_id": str(event.company_id),
                                "name": event.name,
                                "created_at": event.created_at.isoformat(),
                            },
                            event,
                        )
                    )
                elif isinstance(event, ContentOwnerAddedEvent):
                    publish_targets.append(
                        (
                            "company",
                            f"company.{event.company_id}.content-owner.added",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "user_id": str(event.user_id),
                                "company_id": str(event.company_id),
                                "permissions": list(event.permissions),
                                "created_at": event.created_at.isoformat(),
                            },
                            event,
                        )
                    )
                    publish_targets.append(
                        (
                            "content-owner",
                            f"content-owner.{event.content_owner_id}.created",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "user_id": str(event.user_id),
                                "company_id": str(event.company_id),
                                "permissions": list(event.permissions),
                                "created_at": event.created_at.isoformat(),
                            },
                            ContentOwnerCreatedPayload(
                                content_owner_id=event.content_owner_id,
                                user_id=event.user_id,
                                company_id=event.company_id,
                                permissions=event.permissions,
                                created_at=event.created_at,
                            ),
                        )
                    )
                elif isinstance(event, ContentOwnerPermissionsUpdatedEvent):
                    publish_targets.append(
                        (
                            "company",
                            f"company.{event.company_id}.content-owner.permissions-updated",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "company_id": str(event.company_id),
                                "permissions": list(event.permissions),
                                "updated_at": event.updated_at.isoformat(),
                            },
                            event,
                        )
                    )
                    publish_targets.append(
                        (
                            "content-owner",
                            f"content-owner.{event.content_owner_id}.permissions-updated",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "permissions": list(event.permissions),
                                "updated_at": event.updated_at.isoformat(),
                            },
                            ContentOwnerPermissionsUpdatedPayload(
                                content_owner_id=event.content_owner_id,
                                permissions=event.permissions,
                                updated_at=event.updated_at,
                            ),
                        )
                    )
                elif isinstance(event, ContentOwnerRemovedEvent):
                    publish_targets.append(
                        (
                            "company",
                            f"company.{event.company_id}.content-owner.removed",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "company_id": str(event.company_id),
                                "deleted_at": event.deleted_at.isoformat(),
                            },
                            event,
                        )
                    )
                    publish_targets.append(
                        (
                            "content-owner",
                            f"content-owner.{event.content_owner_id}.deleted",
                            {
                                "content_owner_id": str(event.content_owner_id),
                                "deleted_at": event.deleted_at.isoformat(),
                            },
                            ContentOwnerDeletedPayload(
                                content_owner_id=event.content_owner_id,
                                deleted_at=event.deleted_at,
                            ),
                        )
                    )
                else:
                    raise TypeError(
                        f"Can't handle message of type {type(event)}: {event}"
                    )

                for destination_topic, routing_key, body, message in publish_targets:
                    self._outbox_repository.add(
                        message_id=self._uuid_provider.new_v4(),
                        created_at=self._dt_provider.now_utc,
                        destination_topic=destination_topic,
                        routing_key=routing_key,
                        message=message,
                    )

                    await exchanges[destination_topic].publish(
                        aio_pika.Message(
                            body=json.dumps(body).encode(),
                            content_type="application/json",
                        ),
                        routing_key=routing_key,
                    )
        finally:
            await channel.close()
