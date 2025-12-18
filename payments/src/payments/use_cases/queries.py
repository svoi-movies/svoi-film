from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from payments.domain import PaymentStatus
from payments.use_cases.interfaces import PaymentUnitOfWork


@dataclass(frozen=True, slots=True)
class PaymentView:
    id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    description: str | None
    expires_at: datetime
    created_at: datetime
    succeeded_at: datetime | None
    expired_at: datetime | None


class PaymentQueries:
    def __init__(self, uow: PaymentUnitOfWork) -> None:
        self._uow = uow

    async def get_payment(self, payment_id: UUID) -> PaymentView:
        async with self._uow:
            payment = await self._uow.payments.get_by_id(payment_id)
            return PaymentView(
                id=payment.id,  # pyright: ignore[reportAttributeAccessIssue]
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status,
                description=payment.description,
                expires_at=payment.expires_at,
                created_at=payment.created_at,
                succeeded_at=payment.succeeded_at,
                expired_at=payment.expired_at,
            )
