from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from moderator.domain import ModerationRequest, Moderator
from moderator.use_cases.interfaces import (
    AuthService,
    AuthUserData,
    ModerationUnitOfWork,
)


class ModerationCommands:
    def __init__(
        self,
        uow: ModerationUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        auth_service: AuthService,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider
        self._auth_service = auth_service

    async def create_moderator(
        self, user: AuthUserData, bearer_token: str
    ) -> Moderator:
        now = self._datetime_provider.now_utc
        user_id = await self._auth_service.create_moderator_user(
            user=user,
            bearer_token=bearer_token,
        )
        moderator = Moderator.new(
            moderator_id=self._uuid_provider.new_v4(),
            user_id=user_id,
            now=now,
        )
        async with self._uow:
            self._uow.moderators.add(moderator)
            await self._uow.commit()
        return moderator

    async def delete_moderator(self, moderator_id: UUID) -> Moderator:
        now = self._datetime_provider.now_utc
        async with self._uow:
            moderator = await self._uow.moderators.get_by_id(moderator_id)
            moderator.delete(now=now)
            await self._uow.commit()
            return moderator

    async def request_moderation(
        self, episode_id: UUID, content_owner_id: UUID
    ) -> ModerationRequest:
        now = self._datetime_provider.now_utc
        moderation_request = ModerationRequest.new(
            moderation_request_id=self._uuid_provider.new_v4(),
            episode_id=episode_id,
            content_owner_id=content_owner_id,
            now=now,
        )
        async with self._uow:
            self._uow.moderation_requests.add(moderation_request)
            await self._uow.commit()
        return moderation_request

    async def approve_moderation(
        self, moderation_request_id: UUID, moderator_id: UUID
    ) -> ModerationRequest:
        now = self._datetime_provider.now_utc
        async with self._uow:
            moderation_request = (
                await self._uow.moderation_requests.get_by_id(
                    moderation_request_id
                )
            )
            moderation_request.approve(moderator_id=moderator_id, now=now)
            await self._uow.commit()
            return moderation_request

    async def reject_moderation(
        self, moderation_request_id: UUID, moderator_id: UUID
    ) -> ModerationRequest:
        now = self._datetime_provider.now_utc
        async with self._uow:
            moderation_request = (
                await self._uow.moderation_requests.get_by_id(
                    moderation_request_id
                )
            )
            moderation_request.reject(moderator_id=moderator_id, now=now)
            await self._uow.commit()
            return moderation_request
