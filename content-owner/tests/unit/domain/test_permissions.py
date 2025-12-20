from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from commons.ddd.errors import DomainError

from content_owner.domain.content_owner import ContentOwner, ContentOwnerStatus


def test__updating_with_same_permissions_is_noop() -> None:
    now = datetime.now(timezone.utc)
    owner = ContentOwner.new(
        content_owner_id=uuid4(),
        user_id=uuid4(),
        company_id=uuid4(),
        permissions=["upload_titles"],
        now=now,
    )

    owner.update_permissions(["upload_titles"], now + timedelta(minutes=1))

    assert owner.permissions == ("upload_titles",)
    assert owner.updated_at == now


def test__cannot_delete_twice() -> None:
    now = datetime.now(timezone.utc)
    owner = ContentOwner.new(
        content_owner_id=uuid4(),
        user_id=uuid4(),
        company_id=uuid4(),
        permissions=["upload_titles"],
        now=now,
    )

    owner.delete(now + timedelta(minutes=1))

    with pytest.raises(DomainError):
        owner.delete(now + timedelta(minutes=2))
    assert owner.status == ContentOwnerStatus.DELETED
