from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from subscriptions.domain import SubscriptionLevel, SubscriptionStatus
from subscriptions.use_cases.interfaces import SubscriptionUnitOfWork


@dataclass(frozen=True, slots=True)
class SubscriptionView:
    id: UUID
    level: SubscriptionLevel
    status: SubscriptionStatus
    expires_at: datetime
    created_at: datetime
    cancelled_at: datetime | None
    pending_level: SubscriptionLevel | None
    level_change_initiated_at: datetime | None


class SubscriptionQueries:
    def __init__(self, uow: SubscriptionUnitOfWork) -> None:
        self._uow = uow

    async def get_subscription(self, subscription_id: UUID) -> SubscriptionView:
        async with self._uow:
            subscription = await self._uow.subscriptions.get_by_id(subscription_id)
            return SubscriptionView(
                id=subscription.id,  # pyright: ignore[reportAttributeAccessIssue]
                level=subscription.level,
                status=subscription.status,
                expires_at=subscription.expires_at,
                created_at=subscription.created_at,
                cancelled_at=subscription.cancelled_at,
                pending_level=subscription.pending_level,
                level_change_initiated_at=subscription.level_change_initiated_at,
            )
