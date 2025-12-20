from uuid import UUID

import sqlalchemy as sa
from commons.ddd.errors import DomainError
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.domain.moderation_request import ModerationRequest
from moderator.persistence.schema import moderation_requests
from moderator.use_cases.interfaces import ModerationRequestRepository


class SqlAlchemyModerationRequestRepository(ModerationRequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, moderation_request: ModerationRequest) -> None:
        self._session.add(moderation_request)

    async def save(self, moderation_request: ModerationRequest) -> None:
        await self._session.merge(moderation_request)

    async def get_by_id(
        self, moderation_request_id: UUID
    ) -> ModerationRequest:
        result = await self._session.execute(
            sa.select(ModerationRequest).where(
                moderation_requests.c.id == moderation_request_id
            )
        )
        moderation_request = result.scalar_one_or_none()
        if moderation_request is None:
            raise DomainError(
                f"Moderation request {moderation_request_id} not found"
            )
        return moderation_request
