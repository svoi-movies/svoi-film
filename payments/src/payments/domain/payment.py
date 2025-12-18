from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


class PaymentStatus(StrEnum):
    CREATED = "created"
    SUCCEEDED = "succeeded"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True, eq=True)
class PaymentCreatedEvent:
    payment_id: UUID
    amount: Decimal
    currency: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class PaymentSucceededEvent:
    payment_id: UUID
    succeeded_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class PaymentExpiredEvent:
    payment_id: UUID
    expired_at: datetime


class Payment(Aggregate[UUID, Any]):
    def __init__(
        self,
        payment_id: UUID,
        amount: Decimal,
        currency: str,
        status: PaymentStatus,
        description: str | None,
        expires_at: datetime,
        created_at: datetime,
        succeeded_at: datetime | None,
        expired_at: datetime | None,
    ) -> None:
        super().__init__(payment_id)
        self._amount = amount
        self._currency = currency
        self._status = status
        self._description = description
        self._expires_at = expires_at
        self._created_at = created_at
        self._succeeded_at = succeeded_at
        self._expired_at = expired_at

        with Validator() as v:
            v.must(lambda: self._amount > 0, "Payment amount must be positive")
            v.must(lambda: len(self._currency.strip()) > 0, "Currency must not be empty")
            v.must(
                lambda: self._expires_at > self._created_at,
                "Expiration time must be after creation time",
            )

    @reconstructor
    def _init_on_load(self) -> None:
        # When SQLAlchemy loads the entity, __init__ is bypassed.
        # Reset domain events storage so _push_event works.
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        payment_id: UUID,
        amount: Decimal,
        currency: str,
        description: str | None,
        expires_at: datetime,
        now: datetime,
    ) -> "Payment":
        payment = cls(
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.CREATED,
            description=description,
            expires_at=expires_at,
            created_at=now,
            succeeded_at=None,
            expired_at=None,
        )
        payment._push_event(
            PaymentCreatedEvent(
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                created_at=payment.created_at,
                expires_at=payment.expires_at,
            )
        )
        return payment

    def mark_succeeded(self, now: datetime) -> None:
        if self._status == PaymentStatus.SUCCEEDED:
            raise DomainError("Payment is already marked as succeeded")
        if self._status == PaymentStatus.EXPIRED:
            raise DomainError("Cannot succeed an expired payment")

        if now > self._expires_at:
            raise DomainError("Payment can no longer be marked as succeeded after expiry")

        self._status = PaymentStatus.SUCCEEDED
        self._succeeded_at = now
        self._expired_at = None
        self._push_event(PaymentSucceededEvent(payment_id=self.id, succeeded_at=now))

    def expire(self, now: datetime) -> None:
        if self._status == PaymentStatus.EXPIRED:
            raise DomainError("Payment is already expired")
        if self._status == PaymentStatus.SUCCEEDED:
            raise DomainError("Cannot expire a succeeded payment")

        self._status = PaymentStatus.EXPIRED
        self._expired_at = now
        self._push_event(PaymentExpiredEvent(payment_id=self.id, expired_at=now))

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def status(self) -> PaymentStatus:
        return self._status

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def succeeded_at(self) -> datetime | None:
        return self._succeeded_at

    @property
    def expired_at(self) -> datetime | None:
        return self._expired_at
