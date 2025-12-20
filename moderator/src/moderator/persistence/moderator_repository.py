from uuid import UUID

import sqlalchemy as sa
from commons.ddd.errors import DomainError
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.domain.moderator import Moderator
from moderator.persistence.schema import moderators
from moderator.use_cases.interfaces import ModeratorRepository


class SqlAlchemyModeratorRepository(ModeratorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, moderator: Moderator) -> None:
        self._session.add(moderator)

    async def save(self, moderator: Moderator) -> None:
        await self._session.merge(moderator)

    async def get_by_id(self, moderator_id: UUID) -> Moderator:
        result = await self._session.execute(
            sa.select(Moderator).where(moderators.c.id == moderator_id)
        )
        moderator = result.scalar_one_or_none()
        if moderator is None:
            raise DomainError(f"Moderator {moderator_id} not found")
        return moderator
