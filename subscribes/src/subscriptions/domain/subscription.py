from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELED = "canceled"


class SubscriptionLevel(StrEnum):
    L = "L"
    M = "M"


@dataclass(frozen=True, slots=True, eq=True)
class SubscriptionCreatedEvent:
    subscription_id: UUID
    level: SubscriptionLevel
    expires_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class SubscriptionRenewedEvent:
    subscription_id: UUID
    new_expires_at: datetime
    renewed_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class SubscriptionCancelledEvent:
    subscription_id: UUID
    cancelled_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class SubscriptionLevelChangeInitiatedEvent:
    subscription_id: UUID
    target_level: SubscriptionLevel
    initiated_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class SubscriptionLevelChangedEvent:
    subscription_id: UUID
    new_level: SubscriptionLevel
    changed_at: datetime


class Subscription(Aggregate[UUID, Any]):
    def __init__(
        self,
        subscription_id: UUID,
        level: SubscriptionLevel,
        status: SubscriptionStatus,
        expires_at: datetime,
        created_at: datetime,
        cancelled_at: datetime | None,
        pending_level: SubscriptionLevel | None,
        level_change_initiated_at: datetime | None,
    ) -> None:
        super().__init__(subscription_id)
        self._level = level
        self._status = status
        self._expires_at = expires_at
        self._created_at = created_at
        self._cancelled_at = cancelled_at
        self._pending_level = pending_level
        self._level_change_initiated_at = level_change_initiated_at

        with Validator() as v:
            v.must(lambda: self._expires_at > self._created_at, "Expiration time must be in the future")

    @reconstructor
    def _init_on_load(self) -> None:
        # When SQLAlchemy loads the entity, __init__ is bypassed.
        # Reset domain events storage so _push_event works.
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        subscription_id: UUID,
        level: SubscriptionLevel,
        expires_at: datetime,
        now: datetime,
    ) -> "Subscription":
        subscription = cls(
            subscription_id=subscription_id,
            level=level,
            status=SubscriptionStatus.ACTIVE,
            expires_at=expires_at,
            created_at=now,
            cancelled_at=None,
            pending_level=None,
            level_change_initiated_at=None,
        )
        subscription._push_event(
            SubscriptionCreatedEvent(
                subscription_id=subscription.id,
                level=subscription.level,
                expires_at=subscription.expires_at,
                created_at=subscription.created_at,
            )
        )
        return subscription

    def renew(self, new_expires_at: datetime, now: datetime) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise DomainError("Canceled subscription cannot be renewed")
        if new_expires_at <= self._expires_at:
            raise DomainError("New expiration must be after the current expiration")
        if new_expires_at <= now:
            raise DomainError("New expiration must be in the future")

        self._expires_at = new_expires_at
        self._push_event(
            SubscriptionRenewedEvent(
                subscription_id=self.id,
                new_expires_at=new_expires_at,
                renewed_at=now,
            )
        )

    def cancel(self, now: datetime) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise DomainError("Subscription is already canceled")

        self._status = SubscriptionStatus.CANCELED
        self._cancelled_at = now
        self._pending_level = None
        self._level_change_initiated_at = None
        self._push_event(
            SubscriptionCancelledEvent(subscription_id=self.id, cancelled_at=now)
        )

    def initiate_level_change(self, target_level: SubscriptionLevel, now: datetime) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise DomainError("Canceled subscription cannot change level")
        if target_level == self._level:
            raise DomainError("Subscription is already on the requested level")
        if self._pending_level is not None:
            raise DomainError("Level change is already in progress")

        self._pending_level = target_level
        self._level_change_initiated_at = now
        self._push_event(
            SubscriptionLevelChangeInitiatedEvent(
                subscription_id=self.id,
                target_level=target_level,
                initiated_at=now,
            )
        )

    def apply_level_change(self, now: datetime) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise DomainError("Canceled subscription cannot change level")
        if self._pending_level is None:
            raise DomainError("No level change requested")

        self._level = self._pending_level
        self._pending_level = None
        self._level_change_initiated_at = None
        self._push_event(
            SubscriptionLevelChangedEvent(
                subscription_id=self.id,
                new_level=self._level,
                changed_at=now,
            )
        )

    @property
    def level(self) -> SubscriptionLevel:
        return self._level

    @property
    def status(self) -> SubscriptionStatus:
        return self._status

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def cancelled_at(self) -> datetime | None:
        return self._cancelled_at

    @property
    def pending_level(self) -> SubscriptionLevel | None:
        return self._pending_level

    @property
    def level_change_initiated_at(self) -> datetime | None:
        return self._level_change_initiated_at
