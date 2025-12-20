from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from moderator.domain import ModerationRequestStatus, ModeratorStatus
from moderator.use_cases.interfaces import ModerationUnitOfWork


@dataclass(frozen=True, slots=True)
class ModeratorView:
    id: UUID
    user_id: UUID
    status: ModeratorStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ModerationRequestView:
    id: UUID
    episode_id: UUID
    content_owner_id: UUID
    moderator_id: UUID | None
    status: ModerationRequestStatus
    created_at: datetime
    updated_at: datetime


class ModerationQueries:
    def __init__(self, uow: ModerationUnitOfWork) -> None:
        self._uow = uow

    async def get_moderator(self, moderator_id: UUID) -> ModeratorView:
        async with self._uow:
            moderator = await self._uow.moderators.get_by_id(moderator_id)
            return ModeratorView(
                id=moderator.id,  # pyright: ignore[reportAttributeAccessIssue]
                user_id=moderator.user_id,
                status=moderator.status,
                created_at=moderator.created_at,
                updated_at=moderator.updated_at,
            )

    async def get_moderation_request(
        self, moderation_request_id: UUID
    ) -> ModerationRequestView:
        async with self._uow:
            moderation_request = (
                await self._uow.moderation_requests.get_by_id(
                    moderation_request_id
                )
            )
            return ModerationRequestView(
                id=moderation_request.id,  # pyright: ignore[reportAttributeAccessIssue]
                episode_id=moderation_request.episode_id,
                content_owner_id=moderation_request.content_owner_id,
                moderator_id=moderation_request.moderator_id,
                status=moderation_request.status,
                created_at=moderation_request.created_at,
                updated_at=moderation_request.updated_at,
            )
