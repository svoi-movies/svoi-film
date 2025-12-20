import json
from typing import Any, override

import aio_pika
from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractConnection

from streaming.domain import (
    ViewerCreatedEvent,
    ViewerDeletedEvent,
    TitleCreatedEvent,
    EpisodeDraftCreatedEvent,
    EpisodeSourceUploadedEvent,
    EpisodeSourceProcessedEvent,
    EpisodePublishedEvent,
    EpisodeHiddenEvent,
    ViewingSessionCreatedEvent,
    ViewingProgressUpdatedEvent,
    ViewingSessionCompletedEvent,
)
from streaming.persistence.repositories import (
    ViewerRepository,
    TitleRepository,
    EpisodeRepository,
    ViewingSessionRepository,
)


class StreamingUnitOfWork(UnitOfWork[Any]):
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
        self._viewers = ViewerRepository(session)
        self._titles = TitleRepository(session)
        self._episodes = EpisodeRepository(session)
        self._viewing_sessions = ViewingSessionRepository(session)
        self._amqp_connection = amqp_connection

    @property
    def viewers(self) -> ViewerRepository:
        return self._viewers

    @property
    def titles(self) -> TitleRepository:
        return self._titles

    @property
    def episodes(self) -> EpisodeRepository:
        return self._episodes

    @property
    def viewing_sessions(self) -> ViewingSessionRepository:
        return self._viewing_sessions

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
            "streaming", aio_pika.ExchangeType.TOPIC, durable=True
        )
        try:
            for event in events:
                destination_topic = "streaming"

                if isinstance(event, ViewerCreatedEvent):
                    routing_key = f"viewer.{event.viewer_id}.created"
                elif isinstance(event, ViewerDeletedEvent):
                    routing_key = f"viewer.{event.viewer_id}.deleted"
                elif isinstance(event, TitleCreatedEvent):
                    routing_key = f"title.{event.title_id}.created"
                elif isinstance(event, EpisodeDraftCreatedEvent):
                    routing_key = f"episode.{event.episode_id}.draft_created"
                elif isinstance(event, EpisodeSourceUploadedEvent):
                    routing_key = f"episode.{event.episode_id}.source_uploaded"
                elif isinstance(event, EpisodeSourceProcessedEvent):
                    routing_key = f"episode.{event.episode_id}.source_processed"
                elif isinstance(event, EpisodePublishedEvent):
                    routing_key = f"episode.{event.episode_id}.published"
                elif isinstance(event, EpisodeHiddenEvent):
                    routing_key = f"episode.{event.episode_id}.hidden"
                elif isinstance(event, ViewingSessionCreatedEvent):
                    routing_key = f"session.{event.session_id}.created"
                elif isinstance(event, ViewingProgressUpdatedEvent):
                    routing_key = f"session.{event.session_id}.progress_updated"
                elif isinstance(event, ViewingSessionCompletedEvent):
                    routing_key = f"session.{event.session_id}.completed"
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

                # Publish important events immediately
                if isinstance(event, (EpisodePublishedEvent, ViewingSessionCompletedEvent)):
                    body = json.dumps(
                        {
                            **event.__dict__,
                        },
                        default=str,
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
