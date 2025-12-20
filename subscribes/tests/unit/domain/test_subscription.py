from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from commons.ddd.errors import DomainError

from subscriptions.domain.subscription import (
    Subscription,
    SubscriptionLevel,
    SubscriptionStatus,
)


@pytest.fixture()
def subscription() -> Subscription:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return Subscription.new(
        subscription_id=UUID("00000000-0000-0000-0000-000000000001"),
        level=SubscriptionLevel.L,
        expires_at=now + timedelta(days=30),
        now=now,
    )


def test__create_subscription__is_active(subscription: Subscription) -> None:
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.pending_level is None


def test__renew_requires_future_expiration(subscription: Subscription) -> None:
    now = subscription.created_at + timedelta(days=1)
    with pytest.raises(DomainError):
        subscription.renew(new_expires_at=subscription.expires_at, now=now)


def test__initiate_level_change_sets_pending(subscription: Subscription) -> None:
    now = subscription.created_at + timedelta(days=1)
    subscription.initiate_level_change(SubscriptionLevel.M, now)

    assert subscription.pending_level == SubscriptionLevel.M
    assert subscription.level_change_initiated_at == now


def test__apply_without_request_raises(subscription: Subscription) -> None:
    with pytest.raises(DomainError):
        subscription.apply_level_change(subscription.created_at + timedelta(days=1))
