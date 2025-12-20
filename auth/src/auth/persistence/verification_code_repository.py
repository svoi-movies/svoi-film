from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.role import VerificationCode
from auth.persistence.schema import verification_codes
from auth.use_cases.interfaces import VerificationCodeReposiory


class SqlAlchemyVerificationCodeRepository(VerificationCodeReposiory):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.__session = session

    def add(self, code: VerificationCode) -> None:
        self.__session.add(code)

    async def save(self, code: VerificationCode) -> None:
        await self.__session.merge(code)

    async def get_by_user_id(self, user_id: UUID) -> VerificationCode:
        result = await self.__session.execute(
            sa.select(VerificationCode).where(verification_codes.c.user_id == user_id)
        )
        code = result.scalar_one()
        return code
