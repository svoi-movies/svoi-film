from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class ModerationRequestStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True, eq=True)
class ModerationRequestedEvent:
    moderation_request_id: UUID
    episode_id: UUID
    content_owner_id: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ModerationApprovedEvent:
    moderation_request_id: UUID
    episode_id: UUID
    content_owner_id: UUID
    moderator_id: UUID
    approved_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ModerationRejectedEvent:
    moderation_request_id: UUID
    episode_id: UUID
    content_owner_id: UUID
    moderator_id: UUID
    rejected_at: datetime


class ModerationRequest(Aggregate[UUID, Any]):
    def __init__(
        self,
        moderation_request_id: UUID,
        episode_id: UUID,
        content_owner_id: UUID,
        status: ModerationRequestStatus,
        moderator_id: UUID | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(moderation_request_id)
        self._episode_id = episode_id
        self._content_owner_id = content_owner_id
        self._status = status
        self._moderator_id = moderator_id
        self._created_at = created_at
        self._updated_at = updated_at

        with Validator() as v:
            v.must(
                lambda: self._created_at <= self._updated_at,
                "updated_at cannot precede created_at",
            )

    @reconstructor
    def _init_on_load(self) -> None:
        # SQLAlchemy bypasses __init__ on load; reset domain events storage.
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        moderation_request_id: UUID,
        episode_id: UUID,
        content_owner_id: UUID,
        now: datetime,
    ) -> "ModerationRequest":
        moderation_request = cls(
            moderation_request_id=moderation_request_id,
            episode_id=episode_id,
            content_owner_id=content_owner_id,
            status=ModerationRequestStatus.REQUESTED,
            moderator_id=None,
            created_at=now,
            updated_at=now,
        )
        moderation_request._push_event(
            ModerationRequestedEvent(
                moderation_request_id=moderation_request.id,
                episode_id=moderation_request.episode_id,
                content_owner_id=moderation_request.content_owner_id,
                created_at=moderation_request.created_at,
            )
        )
        return moderation_request

    def approve(self, moderator_id: UUID, now: datetime) -> None:
        if self._status != ModerationRequestStatus.REQUESTED:
            raise DomainError("Moderation request is already resolved")

        self._status = ModerationRequestStatus.APPROVED
        self._moderator_id = moderator_id
        self._updated_at = now
        self._push_event(
            ModerationApprovedEvent(
                moderation_request_id=self.id,
                episode_id=self._episode_id,
                content_owner_id=self._content_owner_id,
                moderator_id=moderator_id,
                approved_at=now,
            )
        )

    def reject(self, moderator_id: UUID, now: datetime) -> None:
        if self._status != ModerationRequestStatus.REQUESTED:
            raise DomainError("Moderation request is already resolved")

        self._status = ModerationRequestStatus.REJECTED
        self._moderator_id = moderator_id
        self._updated_at = now
        self._push_event(
            ModerationRejectedEvent(
                moderation_request_id=self.id,
                episode_id=self._episode_id,
                content_owner_id=self._content_owner_id,
                moderator_id=moderator_id,
                rejected_at=now,
            )
        )

    @property
    def episode_id(self) -> UUID:
        return self._episode_id

    @property
    def content_owner_id(self) -> UUID:
        return self._content_owner_id

    @property
    def status(self) -> ModerationRequestStatus:
        return self._status

    @property
    def moderator_id(self) -> UUID | None:
        return self._moderator_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
