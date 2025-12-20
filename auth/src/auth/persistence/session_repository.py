from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.role import Session
from auth.persistence.schema import sessions
from auth.use_cases.interfaces import SessionRepository


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.__session = session

    def add(self, session: Session) -> None:
        self.__session.add(session)

    async def save(self, session: Session) -> None:
        await self.__session.merge(session)

    async def get_by_id(self, session_id: UUID) -> Session:
        result = await self.__session.execute(
            sa.select(Session).where(sessions.c.id == session_id)
        )
        session = result.scalar_one()
        return session

    async def list_by_user_id(self, user_id: UUID) -> list[Session]:
        result = await self.__session.execute(
            sa.select(Session).where(sessions.c.user_id == user_id)
        )
        return list(result.scalars().all())
