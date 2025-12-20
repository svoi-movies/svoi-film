from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from commons.ddd.errors import DomainError

from moderator.domain import Moderator, ModeratorStatus


def test__create_moderator__is_active() -> None:
    now = datetime.now(timezone.utc)
    moderator = Moderator.new(
        moderator_id=uuid4(),
        user_id=uuid4(),
        now=now,
    )

    assert moderator.status == ModeratorStatus.ACTIVE
    assert moderator.updated_at == moderator.created_at


def test__cannot_delete_twice() -> None:
    now = datetime.now(timezone.utc)
    moderator = Moderator.new(
        moderator_id=uuid4(),
        user_id=uuid4(),
        now=now,
    )

    moderator.delete(now + timedelta(minutes=1))

    with pytest.raises(DomainError):
        moderator.delete(now + timedelta(minutes=2))
    assert moderator.status == ModeratorStatus.DELETED
