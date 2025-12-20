from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate
from sqlalchemy.orm import reconstructor


@dataclass(frozen=True, slots=True, eq=True)
class TitleCreatedEvent:
    title_id: UUID
    name: str
    description: str | None
    director: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeDraftAddedEvent:
    title_id: UUID
    episode_id: UUID
    s3_key: str
    added_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeSourceUploadedEvent:
    title_id: UUID
    episode_id: UUID
    uploaded_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeSourceProcessedEvent:
    title_id: UUID
    episode_id: UUID
    processed_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodePublishedEvent:
    title_id: UUID
    episode_id: UUID
    published_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeHiddenEvent:
    title_id: UUID
    episode_id: UUID
    hidden_at: datetime


class Title(Aggregate[UUID, Any]):
    def __init__(
        self,
        title_id: UUID,
        name: str,
        description: str | None,
        director: str | None,
        created_at: datetime,
    ) -> None:
        super().__init__(title_id)
        self._name = name
        self._description = description
        self._director = director
        self._created_at = created_at

    @reconstructor
    def _init_on_load(self) -> None:
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        title_id: UUID,
        name: str,
        description: str | None,
        director: str | None,
        now: datetime,
    ) -> "Title":
        title = cls(
            title_id=title_id,
            name=name,
            description=description,
            director=director,
            created_at=now,
        )
        title._push_event(
            TitleCreatedEvent(
                title_id=title.id,
                name=title.name,
                description=title.description,
                director=title.director,
                created_at=title.created_at,
            )
        )
        return title

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def director(self) -> str | None:
        return self._director

    @property
    def created_at(self) -> datetime:
        return self._created_at
