from typing import Any, override

from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession

from feedback.domain.models import FeedbackCreatedEvent, ScoreChangedEvent
from feedback.persistence.repositories import (
    FeedbackEstimationRepository,
    FeedbackRepository,
    TitleRepository,
    TitleScoreRepository,
)
from feedback.use_cases import interfaces


class FeedbackUnitOfWork(interfaces.FeedbackUnitOfWork, UnitOfWork[Any]):
    def __init__(
        self,
        session: AsyncSession,
        uuid_provider: UUIDProvider,
        dt_provider: DateTimeProvider,
    ) -> None:
        super().__init__(session)
        self._outbox_repository = OutboxRepository(
            session, serializer=DataclassSerializer()
        )
        self._uuid_provider = uuid_provider
        self._dt_provider = dt_provider
        self._titles = TitleRepository(session)
        self._title_scores = TitleScoreRepository(session)
        self._feedbacks = FeedbackRepository(session)
        self._feedback_estimations = FeedbackEstimationRepository(session)

    @property
    def titles(self) -> TitleRepository:
        return self._titles

    @property
    def title_scores(self) -> TitleScoreRepository:
        return self._title_scores

    @property
    def feedbacks(self) -> FeedbackRepository:
        return self._feedbacks

    @property
    def feedback_estimations(self) -> FeedbackEstimationRepository:
        return self._feedback_estimations

    @override
    async def handle_domain_events(self, events: list[Any]) -> None:
        for event in events:
            destination_topic = "ikbo0722.titles"
            if isinstance(event, FeedbackCreatedEvent):
                routing_key = f"feedback.{event.feedback_id}.created"
            elif isinstance(event, ScoreChangedEvent):
                routing_key = f"score.{event.score_id}.changed"
            else:
                raise TypeError(f"Can't handle message of type {type(event)}: {event}")

            self._outbox_repository.add(
                message_id=self._uuid_provider.new_v4(),
                created_at=self._dt_provider.now_utc,
                destination_topic=destination_topic,
                routing_key=routing_key,
                message=event,
            )
