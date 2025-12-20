from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from content_owner.domain import ContentOwner
from content_owner.use_cases.interfaces import (
    AuthService,
    AuthUserData,
    ContentOwnerUnitOfWork,
)


class ContentOwnerCommands:
    def __init__(
        self,
        uow: ContentOwnerUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        auth_service: AuthService,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider
        self._auth_service = auth_service

    async def create_content_owner(
        self,
        user: AuthUserData,
        company_id: UUID,
        permissions: list[str],
        bearer_token: str,
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        user_id = await self._auth_service.create_content_owner_user(
            user=user,
            bearer_token=bearer_token,
        )
        content_owner = ContentOwner.new(
            content_owner_id=self._uuid_provider.new_v4(),
            user_id=user_id,
            company_id=company_id,
            permissions=permissions,
            now=now,
        )
        async with self._uow:
            self._uow.content_owners.add(content_owner)
            await self._uow.commit()
        return content_owner

    async def update_permissions(
        self, content_owner_id: UUID, permissions: list[str]
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(content_owner_id)
            content_owner.update_permissions(permissions, now=now)
            await self._uow.commit()
            return content_owner

    async def delete_content_owner(self, content_owner_id: UUID) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(content_owner_id)
            content_owner.delete(now=now)
            await self._uow.commit()
            return content_owner
