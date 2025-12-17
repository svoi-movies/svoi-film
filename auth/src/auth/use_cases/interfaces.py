from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from commons.unit_of_work.abc import UnitOfWork

from auth.domain.user import User, UserRole
from auth.domain.value_objects import Email


class UserRepository(ABC):

    @abstractmethod
    def add(self, user: User) -> None: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User: ...

    @abstractmethod
    async def find_by_email(self, email: Email) -> User | None: ...


class UserUnitOfWork(UnitOfWork, ABC):
    @property
    @abstractmethod
    def users(self) -> UserRepository: ...


@dataclass(frozen=True, slots=True)
class Token:
    token_type: Literal["Bearer"]
    access_token: str
    refresh_token: str


class JwtIssuer(ABC):

    @abstractmethod
    def issue_token(
        self,
        user_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        session_id: UUID,
        role: UserRole,
    ) -> Token: ...
