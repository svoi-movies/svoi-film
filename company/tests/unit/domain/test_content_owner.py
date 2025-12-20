from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from commons.ddd.errors import DomainError

from company.domain import ContentOwner, ContentOwnerStatus


@pytest.fixture()
def content_owner() -> ContentOwner:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return ContentOwner.new(
        content_owner_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UUID("00000000-0000-0000-0000-000000000100"),
        company_id=UUID("00000000-0000-0000-0000-000000000200"),
        permissions=["upload_titles"],
        now=now,
    )


def test__create_content_owner__is_active(content_owner: ContentOwner) -> None:
    assert content_owner.status == ContentOwnerStatus.ACTIVE
    assert content_owner.permissions == ("upload_titles",)
    assert content_owner.updated_at == content_owner.created_at


def test__update_permissions_changes_state(content_owner: ContentOwner) -> None:
    later = content_owner.created_at + timedelta(minutes=10)
    content_owner.update_permissions(["upload_titles", "edit_titles"], later)

    assert content_owner.permissions == ("upload_titles", "edit_titles")
    assert content_owner.updated_at == later


def test__update_permissions_keeps_order_and_uniqueness(
    content_owner: ContentOwner,
) -> None:
    later = content_owner.created_at + timedelta(minutes=5)
    content_owner.update_permissions(
        ["edit_titles", "edit_titles", "upload_titles"], later
    )

    assert content_owner.permissions == ("edit_titles", "upload_titles")


def test__deleted_owner_cannot_be_updated(content_owner: ContentOwner) -> None:
    content_owner.delete(content_owner.created_at + timedelta(minutes=1))

    with pytest.raises(DomainError):
        content_owner.update_permissions(
            ["upload_titles", "edit_titles"],
            content_owner.created_at + timedelta(minutes=2),
        )


def test__delete_sets_status(content_owner: ContentOwner) -> None:
    content_owner.delete(content_owner.created_at + timedelta(minutes=1))

    assert content_owner.status == ContentOwnerStatus.DELETED
