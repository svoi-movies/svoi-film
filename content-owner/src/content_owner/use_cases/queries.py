from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from content_owner.domain import ContentOwnerStatus
from content_owner.use_cases.interfaces import ContentOwnerUnitOfWork


@dataclass(frozen=True, slots=True)
class ContentOwnerView:
    id: UUID
    user_id: UUID
    company_id: UUID
    permissions: tuple[str, ...]
    status: ContentOwnerStatus
    created_at: datetime
    updated_at: datetime


class ContentOwnerQueries:
    def __init__(self, uow: ContentOwnerUnitOfWork) -> None:
        self._uow = uow

    async def get_content_owner(self, content_owner_id: UUID) -> ContentOwnerView:
        async with self._uow:
            content_owner = await self._uow.content_owners.get_by_id(content_owner_id)
            return ContentOwnerView(
                id=content_owner.id,  # pyright: ignore[reportAttributeAccessIssue]
                user_id=content_owner.user_id,
                company_id=content_owner.company_id,
                permissions=content_owner.permissions,
                status=content_owner.status,
                created_at=content_owner.created_at,
                updated_at=content_owner.updated_at,
            )
