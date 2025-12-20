import json
from typing import Any, override

import aio_pika
from aio_pika.abc import AbstractConnection
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.domain import (
    ModerationApprovedEvent,
    ModerationRejectedEvent,
    ModerationRequestedEvent,
    ModeratorCreatedEvent,
    ModeratorDeletedEvent,
)
from moderator.persistence.moderation_request_repository import (
    SqlAlchemyModerationRequestRepository,
)
from moderator.persistence.moderator_repository import SqlAlchemyModeratorRepository
from moderator.use_cases import interfaces


class ModerationUnitOfWork(UnitOfWork[Any], interfaces.ModerationUnitOfWork):
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
        self._moderators = SqlAlchemyModeratorRepository(session)
        self._moderation_requests = SqlAlchemyModerationRequestRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def moderators(self) -> interfaces.ModeratorRepository:
        return self._moderators

    @property
    def moderation_requests(self) -> interfaces.ModerationRequestRepository:
        return self._moderation_requests

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
                "moderator": await channel.declare_exchange(
                    "moderator", aio_pika.ExchangeType.TOPIC, durable=True
                ),
                "moderation-request": await channel.declare_exchange(
                    "moderation-request",
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                ),
            }
            for event in events:
                publish_targets: list[tuple[str, str, dict[str, Any], Any]] = []
                if isinstance(event, ModeratorCreatedEvent):
                    publish_targets.append(
                        (
                            "moderator",
                            f"moderator.{event.moderator_id}.created",
                            {
                                "moderator_id": str(event.moderator_id),
                                "user_id": str(event.user_id),
                                "created_at": event.created_at.isoformat(),
                            },
                            event,
                        )
                    )
                elif isinstance(event, ModeratorDeletedEvent):
                    publish_targets.append(
                        (
                            "moderator",
                            f"moderator.{event.moderator_id}.deleted",
                            {
                                "moderator_id": str(event.moderator_id),
                                "user_id": str(event.user_id),
                                "deleted_at": event.deleted_at.isoformat(),
                            },
                            event,
                        )
                    )
                elif isinstance(event, ModerationRequestedEvent):
                    publish_targets.append(
                        (
                            "moderation-request",
                            f"moderation-request.{event.moderation_request_id}.requested",
                            {
                                "moderation_request_id": str(
                                    event.moderation_request_id
                                ),
                                "episode_id": str(event.episode_id),
                                "content_owner_id": str(event.content_owner_id),
                                "created_at": event.created_at.isoformat(),
                            },
                            event,
                        )
                    )
                elif isinstance(event, ModerationApprovedEvent):
                    publish_targets.append(
                        (
                            "moderation-request",
                            f"moderation-request.{event.moderation_request_id}.approved",
                            {
                                "moderation_request_id": str(
                                    event.moderation_request_id
                                ),
                                "episode_id": str(event.episode_id),
                                "content_owner_id": str(event.content_owner_id),
                                "moderator_id": str(event.moderator_id),
                                "approved_at": event.approved_at.isoformat(),
                            },
                            event,
                        )
                    )
                elif isinstance(event, ModerationRejectedEvent):
                    publish_targets.append(
                        (
                            "moderation-request",
                            f"moderation-request.{event.moderation_request_id}.rejected",
                            {
                                "moderation_request_id": str(
                                    event.moderation_request_id
                                ),
                                "episode_id": str(event.episode_id),
                                "content_owner_id": str(event.content_owner_id),
                                "moderator_id": str(event.moderator_id),
                                "rejected_at": event.rejected_at.isoformat(),
                            },
                            event,
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
