from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from company.domain import CompanyStatus, ContentOwnerStatus
from company.use_cases.interfaces import CompanyUnitOfWork


@dataclass(frozen=True, slots=True)
class ContentOwnerView:
    id: UUID
    user_id: UUID
    company_id: UUID
    permissions: tuple[str, ...]
    status: ContentOwnerStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CompanyView:
    id: UUID
    name: str
    status: CompanyStatus
    created_at: datetime
    updated_at: datetime


class CompanyQueries:
    def __init__(self, uow: CompanyUnitOfWork) -> None:
        self._uow = uow

    async def get_company(self, company_id: UUID) -> CompanyView:
        async with self._uow:
            company = await self._uow.companies.get_by_id(company_id)
            return CompanyView(
                id=company.id,  # pyright: ignore[reportAttributeAccessIssue]
                name=company.name,
                status=company.status,
                created_at=company.created_at,
                updated_at=company.updated_at,
            )

    async def get_content_owner(
        self, company_id: UUID, content_owner_id: UUID
    ) -> ContentOwnerView:
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_company(
                company_id=company_id,
                content_owner_id=content_owner_id,
            )
            return ContentOwnerView(
                id=content_owner.id,  # pyright: ignore[reportAttributeAccessIssue]
                user_id=content_owner.user_id,
                company_id=content_owner.company_id,
                permissions=content_owner.permissions,
                status=content_owner.status,
                created_at=content_owner.created_at,
                updated_at=content_owner.updated_at,
            )

    async def get_content_owner_by_id(
        self, content_owner_id: UUID
    ) -> ContentOwnerView:
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(
                content_owner_id
            )
            return ContentOwnerView(
                id=content_owner.id,  # pyright: ignore[reportAttributeAccessIssue]
                user_id=content_owner.user_id,
                company_id=content_owner.company_id,
                permissions=content_owner.permissions,
                status=content_owner.status,
                created_at=content_owner.created_at,
                updated_at=content_owner.updated_at,
            )
