from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.role import User
from auth.domain.value_objects import Email
from auth.persistence.schema import users
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
            sa.select(User).where(users.c.id == user_id)
        )
        user = result.scalar_one()
        return user

    async def find_by_email(self, email: Email) -> User | None:
        result = await self.__session.execute(
            sa.select(User).where(users.c.email == email)
        )
        return result.scalar_one_or_none()
