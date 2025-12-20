from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from commons.ddd.errors import DomainError

from moderator.domain import ModerationRequest, ModerationRequestStatus


@pytest.fixture()
def moderation_request() -> ModerationRequest:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return ModerationRequest.new(
        moderation_request_id=UUID("00000000-0000-0000-0000-000000000001"),
        episode_id=UUID("00000000-0000-0000-0000-000000000111"),
        content_owner_id=UUID("00000000-0000-0000-0000-000000000222"),
        now=now,
    )


def test__create_moderation_request__is_requested(
    moderation_request: ModerationRequest,
) -> None:
    assert moderation_request.status == ModerationRequestStatus.REQUESTED
    assert moderation_request.moderator_id is None
    assert moderation_request.updated_at == moderation_request.created_at


def test__approve_changes_state(moderation_request: ModerationRequest) -> None:
    later = moderation_request.created_at + timedelta(minutes=10)
    moderator_id = UUID("00000000-0000-0000-0000-000000000333")
    moderation_request.approve(moderator_id=moderator_id, now=later)

    assert moderation_request.status == ModerationRequestStatus.APPROVED
    assert moderation_request.moderator_id == moderator_id
    assert moderation_request.updated_at == later


def test__reject_changes_state(moderation_request: ModerationRequest) -> None:
    later = moderation_request.created_at + timedelta(minutes=5)
    moderator_id = UUID("00000000-0000-0000-0000-000000000444")
    moderation_request.reject(moderator_id=moderator_id, now=later)

    assert moderation_request.status == ModerationRequestStatus.REJECTED
    assert moderation_request.moderator_id == moderator_id
    assert moderation_request.updated_at == later


def test__resolved_request_cannot_change(
    moderation_request: ModerationRequest,
) -> None:
    later = moderation_request.created_at + timedelta(minutes=1)
    moderation_request.reject(
        moderator_id=UUID("00000000-0000-0000-0000-000000000555"),
        now=later,
    )

    with pytest.raises(DomainError):
        moderation_request.approve(
            moderator_id=UUID("00000000-0000-0000-0000-000000000666"),
            now=later + timedelta(minutes=1),
        )
