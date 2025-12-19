from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from commons.unit_of_work.abc import UnitOfWork

from auth.domain.role import Role, Session, User, VerificationCode
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


class SessionRepository(ABC):

    @abstractmethod
    def add(self, session: Session) -> None: ...

    @abstractmethod
    async def save(self, session: Session) -> None: ...

    @abstractmethod
    async def get_by_id(self, session: UUID) -> Session: ...

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[Session]: ...


class RoleRepository(ABC):

    @abstractmethod
    def add(self, role: Role) -> None: ...

    @abstractmethod
    async def save(self, role: Role) -> None: ...

    @abstractmethod
    async def get_by_id(self, role_id: UUID) -> Role: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Role: ...

    @abstractmethod
    async def list_all(self) -> list[Role]: ...


class VerificationCodeReposiory(ABC):

    @abstractmethod
    def add(self, code: VerificationCode) -> None: ...

    @abstractmethod
    async def save(self, code: VerificationCode) -> None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> VerificationCode: ...


class UserUnitOfWork(UnitOfWork, ABC):
    @property
    @abstractmethod
    def users(self) -> UserRepository: ...

    @property
    @abstractmethod
    def sessions(self) -> SessionRepository: ...

    @property
    @abstractmethod
    def roles(self) -> RoleRepository: ...

    @property
    @abstractmethod
    def verification_codes(self) -> VerificationCodeReposiory: ...


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
        email: Email,
        session_id: UUID,
        role: str,
    ) -> Token: ...
