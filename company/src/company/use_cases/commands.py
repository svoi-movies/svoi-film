from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from company.domain import Company, ContentOwner
from company.use_cases.interfaces import (
    AuthService,
    AuthUserData,
    CompanyUnitOfWork,
)


class CompanyCommands:
    def __init__(
        self,
        uow: CompanyUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        auth_service: AuthService,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider
        self._auth_service = auth_service

    async def create_company(self, name: str) -> Company:
        now = self._datetime_provider.now_utc
        company = Company.new(
            company_id=self._uuid_provider.new_v4(),
            name=name,
            now=now,
        )
        async with self._uow:
            self._uow.companies.add(company)
            await self._uow.commit()
        return company

    async def add_content_owner(
        self,
        company_id: UUID,
        user: AuthUserData,
        permissions: list[str],
        bearer_token: str,
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            await self._uow.companies.get_by_id(company_id)
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

    async def update_content_owner_permissions(
        self, company_id: UUID, content_owner_id: UUID, permissions: list[str]
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_company(
                company_id=company_id,
                content_owner_id=content_owner_id,
            )
            content_owner.update_permissions(permissions, now=now)
            await self._uow.commit()
            return content_owner

    async def update_content_owner_permissions_by_id(
        self, content_owner_id: UUID, permissions: list[str]
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(
                content_owner_id
            )
            content_owner.update_permissions(permissions, now=now)
            await self._uow.commit()
            return content_owner

    async def remove_content_owner(
        self, company_id: UUID, content_owner_id: UUID
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_company(
                company_id=company_id,
                content_owner_id=content_owner_id,
            )
            content_owner.delete(now=now)
            await self._uow.commit()
            return content_owner

    async def remove_content_owner_by_id(
        self, content_owner_id: UUID
    ) -> ContentOwner:
        now = self._datetime_provider.now_utc
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(
                content_owner_id
            )
            content_owner.delete(now=now)
            await self._uow.commit()
            return content_owner
