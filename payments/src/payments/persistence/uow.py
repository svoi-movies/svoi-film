import json
from typing import Any, override

import aio_pika
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractConnection

from payments.domain.payment import (
    PaymentCreatedEvent,
    PaymentExpiredEvent,
    PaymentSucceededEvent,
)
from payments.persistence.payment_repository import SqlAlchemyPaymentRepository
from payments.use_cases import interfaces


class PaymentUnitOfWork(UnitOfWork[Any], interfaces.PaymentUnitOfWork):
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
        self._payments = SqlAlchemyPaymentRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def payments(self) -> interfaces.PaymentRepository:
        return self._payments

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
            "payments", aio_pika.ExchangeType.TOPIC, durable=True
        )
        try:
            for event in events:
                destination_topic = "payments"
                if isinstance(event, PaymentCreatedEvent):
                    routing_key = f"payment.{event.payment_id}.created"
                elif isinstance(event, PaymentSucceededEvent):
                    routing_key = f"payment.{event.payment_id}.succeeded"
                elif isinstance(event, PaymentExpiredEvent):
                    routing_key = f"payment.{event.payment_id}.expired"
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

                if isinstance(event, PaymentSucceededEvent):
                    body = json.dumps(
                        {
                            "payment_id": str(event.payment_id),
                            "succeeded_at": event.succeeded_at.isoformat(),
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
