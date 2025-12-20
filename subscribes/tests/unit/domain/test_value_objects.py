from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from commons.ddd.errors import DomainError

from subscriptions.domain.subscription import Subscription, SubscriptionLevel


def test__cannot_request_same_level() -> None:
    now = datetime.now(timezone.utc)
    subscription = Subscription.new(
        subscription_id=uuid4(),
        level=SubscriptionLevel.L,
        expires_at=now + timedelta(days=30),
        now=now,
    )

    with pytest.raises(DomainError):
        subscription.initiate_level_change(SubscriptionLevel.L, now + timedelta(days=1))


def test__cancel_blocks_level_change() -> None:
    now = datetime.now(timezone.utc)
    subscription = Subscription.new(
        subscription_id=uuid4(),
        level=SubscriptionLevel.L,
        expires_at=now + timedelta(days=30),
        now=now,
    )
    subscription.cancel(now + timedelta(days=1))

    with pytest.raises(DomainError):
        subscription.initiate_level_change(SubscriptionLevel.M, now + timedelta(days=2))
