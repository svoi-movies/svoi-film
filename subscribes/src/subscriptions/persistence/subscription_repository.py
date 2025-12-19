from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from commons.ddd.errors import DomainError

from subscriptions.domain.subscription import Subscription
from subscriptions.persistence.schema import subscriptions
from subscriptions.use_cases.interfaces import SubscriptionRepository


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, subscription: Subscription) -> None:
        self._session.add(subscription)

    async def save(self, subscription: Subscription) -> None:
        await self._session.merge(subscription)

    async def get_by_id(self, subscription_id: UUID) -> Subscription:
        result = await self._session.execute(
            sa.select(Subscription).where(subscriptions.c.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if subscription is None:
            raise DomainError(f"Subscription {subscription_id} not found")
        return subscription
