from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from moderator.domain import Moderator, ModerationRequest


@dataclass(frozen=True, slots=True)
class AuthUserData:
    email: str
    first_name: str
    last_name: str
    password: str


class AuthService(Protocol):
    async def create_moderator_user(
        self, user: AuthUserData, bearer_token: str
    ) -> UUID: ...


class ModeratorRepository(Protocol):
    def add(self, moderator: Moderator) -> None: ...

    async def save(self, moderator: Moderator) -> None: ...

    async def get_by_id(self, moderator_id: UUID) -> Moderator: ...


class ModerationRequestRepository(Protocol):
    def add(self, moderation_request: ModerationRequest) -> None: ...

    async def save(self, moderation_request: ModerationRequest) -> None: ...

    async def get_by_id(
        self, moderation_request_id: UUID
    ) -> ModerationRequest: ...


class ModerationUnitOfWork(ABC):
    @property
    @abstractmethod
    def moderators(self) -> ModeratorRepository: ...

    @property
    @abstractmethod
    def moderation_requests(self) -> ModerationRequestRepository: ...

    @abstractmethod
    async def __aenter__(self) -> None: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
