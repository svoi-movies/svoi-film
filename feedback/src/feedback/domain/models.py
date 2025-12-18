from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError


class Title(Aggregate[UUID, Any]):
    def __init__(
        self,
        title_id: UUID,
        created_at: datetime,
    ) -> None:
        super().__init__(title_id)
        self.created_at = created_at

    @classmethod
    def new(cls, title_id: UUID, now: datetime) -> "Title":
        return cls(title_id=title_id, created_at=now)


class TitleScore(Aggregate[UUID, Any]):
    def __init__(
        self,
        score_id: UUID,
        user_id: UUID,
        title_id: UUID,
        score: int,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(score_id)
        self.user_id = user_id
        self.title_id = title_id
        self.score = score
        self.created_at = created_at
        self.updated_at = updated_at

        with Validator() as v:
            v.must(
                lambda: 1 <= self.score <= 10,
                "Score must be between 1 and 10",
            )

    @classmethod
    def new(
        cls,
        score_id: UUID,
        user_id: UUID,
        title_id: UUID,
        score: int,
        now: datetime,
    ) -> "TitleScore":
        return cls(
            score_id=score_id,
            user_id=user_id,
            title_id=title_id,
            score=score,
            created_at=now,
            updated_at=now,
        )

    def update_score(self, score: int, now: datetime) -> None:
        with Validator() as v:
            v.must(
                lambda: 1 <= score <= 10,
                "Score must be between 1 and 10",
            )
        self.score = score
        self.updated_at = now


class Feedback(Aggregate[UUID, Any]):
    def __init__(
        self,
        feedback_id: UUID,
        user_id: UUID,
        title_id: UUID,
        text: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(feedback_id)
        self.user_id = user_id
        self.title_id = title_id
        self.text = text
        self.created_at = created_at
        self.updated_at = updated_at

        with Validator() as v:
            v.must(
                lambda: len(self.text.strip()) > 0,
                "Feedback text cannot be empty",
            )
            v.must(
                lambda: len(self.text) <= 5000,
                "Feedback text must not exceed 5000 characters",
            )

    @classmethod
    def new(
        cls,
        feedback_id: UUID,
        user_id: UUID,
        title_id: UUID,
        text: str,
        now: datetime,
    ) -> "Feedback":
        return cls(
            feedback_id=feedback_id,
            user_id=user_id,
            title_id=title_id,
            text=text,
            created_at=now,
            updated_at=now,
        )

    def update_text(self, text: str, now: datetime) -> None:
        with Validator() as v:
            v.must(
                lambda: len(text.strip()) > 0,
                "Feedback text cannot be empty",
            )
            v.must(
                lambda: len(text) <= 5000,
                "Feedback text must not exceed 5000 characters",
            )
        self.text = text
        self.updated_at = now


class FeedbackEstimation(Aggregate[UUID, Any]):
    def __init__(
        self,
        estimation_id: UUID,
        user_id: UUID,
        feedback_id: UUID,
        is_positive: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(estimation_id)
        self.user_id = user_id
        self.feedback_id = feedback_id
        self.is_positive = is_positive
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def new(
        cls,
        estimation_id: UUID,
        user_id: UUID,
        feedback_id: UUID,
        is_positive: bool,
        now: datetime,
    ) -> "FeedbackEstimation":
        return cls(
            estimation_id=estimation_id,
            user_id=user_id,
            feedback_id=feedback_id,
            is_positive=is_positive,
            created_at=now,
            updated_at=now,
        )

    def update(self, is_positive: bool, now: datetime) -> None:
        self.is_positive = is_positive
        self.updated_at = now


@dataclass(slots=True, frozen=True, eq=True)
class FeedbackCreatedEvent:
    feedback_id: UUID
    user_id: UUID
    title_id: UUID
    created_at: datetime


@dataclass(slots=True, frozen=True, eq=True)
class ScoreChangedEvent:
    score_id: UUID
    user_id: UUID
    title_id: UUID
    old_score: int | None
    new_score: int
    changed_at: datetime
