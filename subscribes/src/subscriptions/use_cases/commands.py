from datetime import datetime
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from subscriptions.domain import Subscription, SubscriptionLevel
from subscriptions.use_cases.interfaces import SubscriptionUnitOfWork


class SubscriptionCommands:
    def __init__(
        self,
        uow: SubscriptionUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider

    async def create_subscription(
        self,
        level: SubscriptionLevel,
        expires_at: datetime,
    ) -> Subscription:
        now = self._datetime_provider.now_utc
        subscription = Subscription.new(
            subscription_id=self._uuid_provider.new_v4(),
            level=level,
            expires_at=expires_at,
            now=now,
        )
        async with self._uow:
            self._uow.subscriptions.add(subscription)
            await self._uow.commit()
        return subscription

    async def renew_subscription(
        self, subscription_id: UUID, new_expires_at: datetime
    ) -> Subscription:
        now = self._datetime_provider.now_utc
        async with self._uow:
            subscription = await self._uow.subscriptions.get_by_id(subscription_id)
            subscription.renew(new_expires_at=new_expires_at, now=now)
            await self._uow.commit()
            return subscription

    async def cancel_subscription(self, subscription_id: UUID) -> Subscription:
        now = self._datetime_provider.now_utc
        async with self._uow:
            subscription = await self._uow.subscriptions.get_by_id(subscription_id)
            subscription.cancel(now)
            await self._uow.commit()
            return subscription

    async def initiate_level_change(
        self, subscription_id: UUID, target_level: SubscriptionLevel
    ) -> Subscription:
        now = self._datetime_provider.now_utc
        async with self._uow:
            subscription = await self._uow.subscriptions.get_by_id(subscription_id)
            subscription.initiate_level_change(target_level=target_level, now=now)
            await self._uow.commit()
            return subscription

    async def apply_level_change(self, subscription_id: UUID) -> Subscription:
        now = self._datetime_provider.now_utc
        async with self._uow:
            subscription = await self._uow.subscriptions.get_by_id(subscription_id)
            subscription.apply_level_change(now)
            await self._uow.commit()
            return subscription
