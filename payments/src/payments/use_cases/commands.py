from datetime import datetime
from decimal import Decimal
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from payments.domain import Payment
from payments.use_cases.interfaces import PaymentUnitOfWork


class PaymentsCommands:
    def __init__(
        self,
        uow: PaymentUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        description: str | None,
        expires_at: datetime,
    ) -> Payment:
        now = self._datetime_provider.now_utc
        payment = Payment.new(
            payment_id=self._uuid_provider.new_v4(),
            amount=amount,
            currency=currency,
            description=description,
            expires_at=expires_at,
            now=now,
        )
        async with self._uow:
            self._uow.payments.add(payment)
            await self._uow.commit()
        return payment

    async def mark_payment_succeeded(self, payment_id: UUID) -> Payment:
        now = self._datetime_provider.now_utc
        async with self._uow:
            payment = await self._uow.payments.get_by_id(payment_id)
            payment.mark_succeeded(now)
            await self._uow.commit()
            return payment

    async def mark_payment_expired(self, payment_id: UUID) -> Payment:
        now = self._datetime_provider.now_utc
        async with self._uow:
            payment = await self._uow.payments.get_by_id(payment_id)
            payment.expire(now)
            await self._uow.commit()
            return payment
