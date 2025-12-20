from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class EpisodeStatus(StrEnum):
    DRAFT = "draft"
    SOURCE_UPLOADED = "source_uploaded"
    SOURCE_PROCESSED = "source_processed"
    PUBLISHED = "published"
    HIDDEN = "hidden"


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeDraftCreatedEvent:
    episode_id: UUID
    title_id: UUID
    s3_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeSourceUploadedEvent:
    episode_id: UUID
    uploaded_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeSourceProcessedEvent:
    episode_id: UUID
    processed_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodePublishedEvent:
    episode_id: UUID
    published_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class EpisodeHiddenEvent:
    episode_id: UUID
    hidden_at: datetime


class Episode(Aggregate[UUID, Any]):
    def __init__(
        self,
        episode_id: UUID,
        title_id: UUID,
        s3_key: str,
        status: EpisodeStatus,
        created_at: datetime,
        name: str,
        description: str | None = None,
        duration: int | None = None,
        uploaded_at: datetime | None = None,
        processed_at: datetime | None = None,
        published_at: datetime | None = None,
        hidden_at: datetime | None = None,
    ) -> None:
        super().__init__(episode_id)
        self._title_id = title_id
        self._s3_key = s3_key
        self._status = status
        self._created_at = created_at
        self._name = name
        self._description = description
        self._duration = duration
        self._uploaded_at = uploaded_at
        self._processed_at = processed_at
        self._published_at = published_at
        self._hidden_at = hidden_at

        with Validator() as v:
            v.must(lambda: len(self._s3_key.strip()) > 0, "S3 key must not be empty")
            v.must(lambda: len(self._name.strip()) > 0, "Episode name must not be empty")

    @reconstructor
    def _init_on_load(self) -> None:
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        episode_id: UUID,
        title_id: UUID,
        s3_key: str,
        name: str,
        now: datetime,
        description: str | None = None,
        duration: int | None = None,
    ) -> "Episode":
        episode = cls(
            episode_id=episode_id,
            title_id=title_id,
            s3_key=s3_key,
            name=name,
            description=description,
            duration=duration,
            status=EpisodeStatus.DRAFT,
            created_at=now,
        )
        episode._push_event(
            EpisodeDraftCreatedEvent(
                episode_id=episode.id,
                title_id=title_id,
                s3_key=s3_key,
                created_at=now,
            )
        )
        return episode

    def upload_source(self, now: datetime) -> None:
        if self._status != EpisodeStatus.DRAFT:
            raise DomainError("Can only upload source for draft episodes")

        self._status = EpisodeStatus.SOURCE_UPLOADED
        self._uploaded_at = now
        self._push_event(EpisodeSourceUploadedEvent(episode_id=self.id, uploaded_at=now))

    def process_source(self, now: datetime) -> None:
        if self._status != EpisodeStatus.SOURCE_UPLOADED:
            raise DomainError("Can only process uploaded episodes")

        self._status = EpisodeStatus.SOURCE_PROCESSED
        self._processed_at = now
        self._push_event(EpisodeSourceProcessedEvent(episode_id=self.id, processed_at=now))

    def publish(self, now: datetime) -> None:
        if self._status != EpisodeStatus.SOURCE_PROCESSED:
            raise DomainError("Can only publish processed episodes")

        self._status = EpisodeStatus.PUBLISHED
        self._published_at = now
        self._push_event(EpisodePublishedEvent(episode_id=self.id, published_at=now))

    def hide(self, now: datetime) -> None:
        if self._status != EpisodeStatus.PUBLISHED:
            raise DomainError("Can only hide published episodes")

        self._status = EpisodeStatus.HIDDEN
        self._hidden_at = now
        self._push_event(EpisodeHiddenEvent(episode_id=self.id, hidden_at=now))

    @property
    def title_id(self) -> UUID:
        return self._title_id

    @property
    def s3_key(self) -> str:
        return self._s3_key

    @property
    def status(self) -> EpisodeStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def duration(self) -> int | None:
        return self._duration

    @property
    def uploaded_at(self) -> datetime | None:
        return self._uploaded_at

    @property
    def processed_at(self) -> datetime | None:
        return self._processed_at

    @property
    def published_at(self) -> datetime | None:
        return self._published_at

    @property
    def hidden_at(self) -> datetime | None:
        return self._hidden_at
