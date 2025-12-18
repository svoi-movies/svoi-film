from dataclasses import dataclass
from uuid import UUID

from auth.use_cases.interfaces import UserUnitOfWork


@dataclass(frozen=True, slots=True)
class GetMeResult:
    id: UUID
    email: str
    first_name: str
    last_name: str


class UserQueries:

    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def get_me(self, user_id: UUID) -> GetMeResult:
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            return GetMeResult(
                id=user.id,  # pyright: ignore[reportArgumentType]
                email=user.email.value,
                first_name=user.first_name,
                last_name=user.last_name,
            )
