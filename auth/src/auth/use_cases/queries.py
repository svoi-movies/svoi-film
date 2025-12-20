from dataclasses import dataclass
from uuid import UUID

from auth.use_cases.interfaces import UserUnitOfWork


@dataclass(frozen=True, slots=True)
class GetMeResult:
    id: UUID
    email: str
    first_name: str
    last_name: str


@dataclass(frozen=True, slots=True)
class RoleResult:
    id: UUID
    name: str
    allow_self_registration: bool
    creator_role_id: UUID | None


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

    async def list_roles(self) -> list[RoleResult]:
        async with self._uow:
            roles = await self._uow.roles.list_all()
            return [
                RoleResult(
                    id=role.id,  # pyright: ignore[reportArgumentType]
                    name=role.name,
                    allow_self_registration=role.allow_self_registration,
                    creator_role_id=role.creator_role_id,
                )
                for role in roles
            ]
