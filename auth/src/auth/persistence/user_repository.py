from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload

from auth.entities.user import Session, User
from auth.entities.value_objects import Email
from auth.persistence.schema import mapper_registry
from auth.use_cases.interfaces import UserRepository


class SqlAlchemyUserRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.__session = session

    def add(self, user: User) -> None:
        self.__session.add(user)

    async def save(self, user: User) -> None:
        await self.__session.merge(user)

    async def get_by_id(self, user_id: UUID) -> User:
        result = await self.__session.execute(
            sa.select(User)
            .where(users.c.id == user_id)
            .options(selectinload(User._sessions))
        )
        user = result.scalar_one()
        return user

    async def find_by_email(self, email: Email) -> User | None:
        result = await self.__session.execute(
            sa.select(User)
            .where(users.c.email == email)
            .options(selectinload(User._sessions))
        )
        return result.scalar_one_or_none()
