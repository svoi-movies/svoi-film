from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.role import Role
from auth.persistence.schema import roles, users
from auth.use_cases.interfaces import RoleRepository


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.__session = session

    def add(self, role: Role) -> None:
        self.__session.add(role)

    async def save(self, role: Role) -> None:
        await self.__session.merge(role)

    async def get_by_id(self, role_id: UUID) -> Role:
        result = await self.__session.execute(
            sa.select(Role).where(roles.c.id == role_id)
        )
        role = result.scalar_one()
        return role

    async def get_by_name(self, name: str) -> Role:
        result = await self.__session.execute(
            sa.select(Role).where(roles.c.name == name)
        )
        role = result.scalar_one()
        return role

    async def get_by_user_id(self, user_id: UUID) -> Role:
        result = await self.__session.execute(
            sa.select(Role)
            .join(users, users.c.role_id == roles.c.id)
            .where(users.c.id == user_id)
        )
        role = result.scalar_one()
        return role

    async def list_all(self) -> list[Role]:
        result = await self.__session.execute(sa.select(Role))
        return list(result.scalars().all())
