from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Tuple
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class ContentOwnerStatus(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True, eq=True)
class ContentOwnerAddedEvent:
    content_owner_id: UUID
    user_id: UUID
    company_id: UUID
    permissions: Tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ContentOwnerPermissionsUpdatedEvent:
    content_owner_id: UUID
    company_id: UUID
    permissions: Tuple[str, ...]
    updated_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ContentOwnerRemovedEvent:
    content_owner_id: UUID
    company_id: UUID
    deleted_at: datetime


class ContentOwner(Aggregate[UUID, Any]):
    def __init__(
        self,
        content_owner_id: UUID,
        user_id: UUID,
        company_id: UUID,
        permissions: Iterable[str],
        status: ContentOwnerStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(content_owner_id)
        self._user_id = user_id
        self._company_id = company_id
        self._permissions = self._normalize_permissions(permissions)
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at

        with Validator() as v:
            v.must(lambda: self._created_at <= self._updated_at, "updated_at cannot precede created_at")

    @reconstructor
    def _init_on_load(self) -> None:
        # SQLAlchemy bypasses __init__ on load; reset domain events storage.
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        content_owner_id: UUID,
        user_id: UUID,
        company_id: UUID,
        permissions: Iterable[str],
        now: datetime,
    ) -> "ContentOwner":
        content_owner = cls(
            content_owner_id=content_owner_id,
            user_id=user_id,
            company_id=company_id,
            permissions=permissions,
            status=ContentOwnerStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        content_owner._push_event(
            ContentOwnerAddedEvent(
                content_owner_id=content_owner.id,
                user_id=content_owner.user_id,
                company_id=content_owner.company_id,
                permissions=content_owner.permissions,
                created_at=content_owner.created_at,
            )
        )
        return content_owner

    def update_permissions(self, permissions: Iterable[str], now: datetime) -> None:
        if self._status == ContentOwnerStatus.DELETED:
            raise DomainError("Deleted content owner cannot be updated")

        new_permissions = self._normalize_permissions(permissions)
        if new_permissions == self._permissions:
            return

        self._permissions = new_permissions
        self._updated_at = now
        self._push_event(
            ContentOwnerPermissionsUpdatedEvent(
                content_owner_id=self.id,
                company_id=self._company_id,
                permissions=self._permissions,
                updated_at=now,
            )
        )

    def delete(self, now: datetime) -> None:
        if self._status == ContentOwnerStatus.DELETED:
            raise DomainError("Content owner already deleted")

        self._status = ContentOwnerStatus.DELETED
        self._updated_at = now
        self._push_event(
            ContentOwnerRemovedEvent(
                content_owner_id=self.id,
                company_id=self._company_id,
                deleted_at=now,
            )
        )

    @staticmethod
    def _normalize_permissions(permissions: Iterable[str]) -> Tuple[str, ...]:
        # Preserve order, drop duplicates.
        return tuple(dict.fromkeys(permissions))

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def company_id(self) -> UUID:
        return self._company_id

    @property
    def permissions(self) -> Tuple[str, ...]:
        return self._permissions

    @property
    def status(self) -> ContentOwnerStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
