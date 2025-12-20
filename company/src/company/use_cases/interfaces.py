from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from company.domain import Company, ContentOwner


@dataclass(frozen=True, slots=True)
class AuthUserData:
    email: str
    first_name: str
    last_name: str
    password: str


class AuthService(Protocol):
    async def create_content_owner_user(
        self, user: AuthUserData, bearer_token: str
    ) -> UUID: ...


class CompanyRepository(Protocol):
    def add(self, company: Company) -> None: ...

    async def save(self, company: Company) -> None: ...

    async def get_by_id(self, company_id: UUID) -> Company: ...


class ContentOwnerRepository(Protocol):
    def add(self, content_owner: ContentOwner) -> None: ...

    async def save(self, content_owner: ContentOwner) -> None: ...

    async def get_by_id(self, content_owner_id: UUID) -> ContentOwner: ...

    async def get_by_company(
        self, company_id: UUID, content_owner_id: UUID
    ) -> ContentOwner: ...


class CompanyUnitOfWork(ABC):
    @property
    @abstractmethod
    def companies(self) -> CompanyRepository: ...

    @property
    @abstractmethod
    def content_owners(self) -> ContentOwnerRepository: ...

    @abstractmethod
    async def __aenter__(self) -> None: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
