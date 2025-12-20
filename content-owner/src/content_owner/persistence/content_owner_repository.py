from uuid import UUID

import sqlalchemy as sa
from commons.ddd.errors import DomainError
from sqlalchemy.ext.asyncio import AsyncSession

from content_owner.domain.content_owner import ContentOwner
from content_owner.persistence.schema import content_owners
from content_owner.use_cases.interfaces import ContentOwnerRepository


class SqlAlchemyContentOwnerRepository(ContentOwnerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, content_owner: ContentOwner) -> None:
        self._session.add(content_owner)

    async def save(self, content_owner: ContentOwner) -> None:
        await self._session.merge(content_owner)

    async def get_by_id(self, content_owner_id: UUID) -> ContentOwner:
        result = await self._session.execute(
            sa.select(ContentOwner).where(content_owners.c.id == content_owner_id)
        )
        content_owner = result.scalar_one_or_none()
        if content_owner is None:
            raise DomainError(f"Content owner {content_owner_id} not found")
        return content_owner
