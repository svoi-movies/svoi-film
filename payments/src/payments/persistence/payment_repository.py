from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from payments.domain.payment import Payment
from payments.persistence.schema import payments
from payments.use_cases.interfaces import PaymentRepository


class SqlAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, payment: Payment) -> None:
        self._session.add(payment)

    async def save(self, payment: Payment) -> None:
        await self._session.merge(payment)

    async def get_by_id(self, payment_id: UUID) -> Payment:
        result = await self._session.execute(
            sa.select(Payment).where(payments.c.id == payment_id)
        )
        return result.scalar_one()
