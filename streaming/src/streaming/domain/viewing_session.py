from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


@dataclass(frozen=True, slots=True, eq=True)
class ViewingSessionCreatedEvent:
    session_id: UUID
    viewer_id: UUID
    episode_id: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ViewingProgressUpdatedEvent:
    session_id: UUID
    progress_seconds: int
    updated_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ViewingSessionCompletedEvent:
    session_id: UUID
    completed_at: datetime


class ViewingSession(Aggregate[UUID, Any]):
    def __init__(
        self,
        session_id: UUID,
        viewer_id: UUID,
        episode_id: UUID,
        progress_seconds: int,
        created_at: datetime,
        completed_at: datetime | None = None,
    ) -> None:
        super().__init__(session_id)
        self._viewer_id = viewer_id
        self._episode_id = episode_id
        self._progress_seconds = progress_seconds
        self._created_at = created_at
        self._completed_at = completed_at

        with Validator() as v:
            v.must(lambda: self._progress_seconds >= 0, "Progress must be non-negative")

    @reconstructor
    def _init_on_load(self) -> None:
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        session_id: UUID,
        viewer_id: UUID,
        episode_id: UUID,
        now: datetime,
    ) -> "ViewingSession":
        session = cls(
            session_id=session_id,
            viewer_id=viewer_id,
            episode_id=episode_id,
            progress_seconds=0,
            created_at=now,
            completed_at=None,
        )
        session._push_event(
            ViewingSessionCreatedEvent(
                session_id=session.id,
                viewer_id=viewer_id,
                episode_id=episode_id,
                created_at=now,
            )
        )
        return session

    def update_progress(self, progress_seconds: int, now: datetime) -> None:
        if self._completed_at is not None:
            raise DomainError("Cannot update progress on completed session")

        if progress_seconds < 0:
            raise DomainError("Progress must be non-negative")

        self._progress_seconds = progress_seconds
        self._push_event(
            ViewingProgressUpdatedEvent(
                session_id=self.id,
                progress_seconds=progress_seconds,
                updated_at=now,
            )
        )

    def complete(self, now: datetime) -> None:
        if self._completed_at is not None:
            raise DomainError("Session is already completed")

        self._completed_at = now
        self._push_event(ViewingSessionCompletedEvent(session_id=self.id, completed_at=now))

    @property
    def viewer_id(self) -> UUID:
        return self._viewer_id

    @property
    def episode_id(self) -> UUID:
        return self._episode_id

    @property
    def progress_seconds(self) -> int:
        return self._progress_seconds

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def is_completed(self) -> bool:
        return self._completed_at is not None
