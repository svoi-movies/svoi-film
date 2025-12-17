from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from commons.ddd import Aggregate, DomainError, Entity

from .value_objects import Email, UserPassword


class UserRole(str, Enum):
    ADMIN = "admin"
    VIEWER = "viewer"
    MODERATOR = "moderator"
    CONTENT_OWNER = "content_owner"


class UserStatus(str, Enum):
    NON_ACTIVE = "non_active"
    ACTIVE = "active"
    SUSPENDED = "suspend"


class PasswordHasher(Protocol):

    def hash_password(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class Session(Entity[UUID]):

    TTL = timedelta(days=2)

    def __init__(
        self,
        session_id: UUID,
        user_id: UUID,
        created_at: datetime,
        expires_at: datetime,
        closed_at: datetime | None,
    ) -> None:
        super().__init__(session_id)
        self._created_at = created_at
        self._expires_at = expires_at
        self._closed_at = closed_at
        self._user_id = user_id

    @classmethod
    def new(cls, session_id: UUID, user_id: UUID, now: datetime) -> "Session":
        return Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + cls.TTL,
            closed_at=None,
        )

    def is_active_now(self, now: datetime) -> bool:
        return self._expires_at >= now and self._closed_at is None

    def close(self, now: datetime) -> None:
        if not self.is_active_now(now):
            raise DomainError("Can't close closed session")

        self._closed_at = now

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def created_at(self) -> datetime:
        return self._created_at


class User(Aggregate[UUID, Any]):

    def __init__(
        self,
        user_id: UUID,
        email: Email,
        first_name: str,
        last_name: str,
        status: UserStatus,
        role: UserRole,
        password_hash: str,
        email_verified: bool,
        must_reset_password: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(user_id)
        self._first_name = first_name
        self._last_name = last_name
        self._email_verified = email_verified
        self._must_reset_password = must_reset_password
        self._role = role
        self._status = status
        self._password_hash = password_hash
        self._email = email
        self._sessions: list[Session] = []
        self._created_at = created_at

    @property
    def email(self) -> Email:
        return self._email

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> UserRole:
        return self._role

    def try_activate(self) -> None:
        if self._email_verified and not self._must_reset_password:
            self._status = UserStatus.ACTIVE

    def set_password(
        self,
        password: UserPassword,
        password_hasher: PasswordHasher,
    ) -> None:
        self._password_hash = password_hasher.hash_password(password.value)
        self._must_reset_password = False

    @classmethod
    def create_viewer(
        cls,
        user_id: UUID,
        email: Email,
        first_name: str,
        last_name: str,
        password: UserPassword,
        hasher: PasswordHasher,
        created_at: datetime,
    ) -> "User":
        return User(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=hasher.hash_password(password.value),
            email_verified=False,
            must_reset_password=False,
            role=UserRole.VIEWER,
            status=UserStatus.NON_ACTIVE,
            created_at=created_at,
        )

    def create_session(
        self,
        session_id: UUID,
        now: datetime,
    ) -> "Session":
        session = Session.new(
            session_id=session_id,
            user_id=self.id,  # pyright: ignore[reportArgumentType]
            now=now,
        )
        self._sessions.append(session)
        return session

    def close_session(self, session_id: UUID, now: datetime) -> None:
        session = next((s for s in self._sessions if s.id == session_id), None)
        if session is None:
            raise DomainError(f"Unknown session with id {session_id}")

        return session.close(now)
