from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class ModeratorStatus(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True, eq=True)
class ModeratorCreatedEvent:
    moderator_id: UUID
    user_id: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ModeratorDeletedEvent:
    moderator_id: UUID
    user_id: UUID
    deleted_at: datetime


class Moderator(Aggregate[UUID, Any]):
    def __init__(
        self,
        moderator_id: UUID,
        user_id: UUID,
        status: ModeratorStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(moderator_id)
        self._user_id = user_id
        self._status = status
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
    def new(cls, moderator_id: UUID, user_id: UUID, now: datetime) -> "Moderator":
        moderator = cls(
            moderator_id=moderator_id,
            user_id=user_id,
            status=ModeratorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        moderator._push_event(
            ModeratorCreatedEvent(
                moderator_id=moderator.id,
                user_id=moderator.user_id,
                created_at=moderator.created_at,
            )
        )
        return moderator

    def delete(self, now: datetime) -> None:
        if self._status == ModeratorStatus.DELETED:
            raise DomainError("Moderator already deleted")

        self._status = ModeratorStatus.DELETED
        self._updated_at = now
        self._push_event(
            ModeratorDeletedEvent(
                moderator_id=self.id,
                user_id=self._user_id,
                deleted_at=now,
            )
        )

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def status(self) -> ModeratorStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
