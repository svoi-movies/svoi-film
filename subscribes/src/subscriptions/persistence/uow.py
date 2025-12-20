import json
from typing import Any, override

import aio_pika
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractConnection

from subscriptions.domain.subscription import (
    SubscriptionCancelledEvent,
    SubscriptionCreatedEvent,
    SubscriptionLevelChangeInitiatedEvent,
    SubscriptionLevelChangedEvent,
    SubscriptionRenewedEvent,
)
from subscriptions.persistence.subscription_repository import (
    SqlAlchemySubscriptionRepository,
)
from subscriptions.use_cases import interfaces


class SubscriptionUnitOfWork(UnitOfWork[Any], interfaces.SubscriptionUnitOfWork):
    """
    Wraps the SQLAlchemy session and routes domain events to the outbox.
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
        self._subscriptions = SqlAlchemySubscriptionRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def subscriptions(self) -> interfaces.SubscriptionRepository:
        return self._subscriptions

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
            "subscriptions", aio_pika.ExchangeType.TOPIC, durable=True
        )
        try:
            for event in events:
                destination_topic = "subscriptions"
                if isinstance(event, SubscriptionCreatedEvent):
                    routing_key = f"subscription.{event.subscription_id}.created"
                elif isinstance(event, SubscriptionRenewedEvent):
                    routing_key = f"subscription.{event.subscription_id}.renewed"
                elif isinstance(event, SubscriptionCancelledEvent):
                    routing_key = f"subscription.{event.subscription_id}.cancelled"
                elif isinstance(event, SubscriptionLevelChangeInitiatedEvent):
                    routing_key = f"sub.{event.subscription_id}.lvl-change-requested"
                elif isinstance(event, SubscriptionLevelChangedEvent):
                    routing_key = f"subscription.{event.subscription_id}.level-changed"
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

                if isinstance(event, SubscriptionLevelChangedEvent):
                    body = json.dumps(
                        {
                            "subscription_id": str(event.subscription_id),
                            "new_level": event.new_level.value,
                            "changed_at": event.changed_at.isoformat(),
                        }
                    ).encode()
                    await exchange.publish(
                        aio_pika.Message(
                            body=body,
                            content_type="application/json",
                        ),
                        routing_key=routing_key,
                    )
        finally:
            await channel.close()
