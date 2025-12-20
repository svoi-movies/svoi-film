from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError

from auth.domain.value_objects import Email, UserPassword


@dataclass(frozen=True)
class UserCreatedEvent:
    user_id: UUID
    email: str
    role_id: UUID
    first_name: str
    last_name: str


class PasswordService(Protocol):
    def hash_password(self, password: UserPassword) -> str: ...

    def verify(self, password: UserPassword, password_hash: str) -> bool: ...


class Role(Aggregate[UUID, Any]):
    def __init__(
        self,
        role_id: UUID,
        name: str,
        allow_self_registration: bool,
        creator_role_id: UUID | None = None,
    ) -> None:
        super().__init__(role_id)
        self.name = name
        self.allow_self_registration = allow_self_registration
        self.creator_role_id = creator_role_id

    @classmethod
    def new(
        cls,
        role_id: UUID,
        name: str,
        allow_self_registration: bool,
        creator_role_id: UUID | None = None,
    ) -> "Role":
        return Role(
            role_id=role_id,
            name=name,
            allow_self_registration=allow_self_registration,
            creator_role_id=creator_role_id,
        )


class VerificationCode(Aggregate[UUID, Any]):
    def __init__(
        self,
        code_id: UUID,
        user_id: UUID,
        code: str,
        valid_until: datetime,
        created_at: datetime,
    ) -> None:
        super().__init__(code_id)
        self.user_id = user_id
        self.code = code
        self.valid_until = valid_until
        self.created_at = created_at

        with Validator() as v:
            v.must_regexp_full_match(
                r"\d\d\d-\d\d\d",
                self.code,
                "Verification code must match the pattern 000-000",
            )
            v.must(
                lambda: self.valid_until > self.created_at,
                "Valid until must be greater than creation time",
            )

    def verify(self, entered_code: str, now: datetime) -> None:
        if now >= self.valid_until:
            raise DomainError("Verification code has expired")

        if not self.code == entered_code:
            raise DomainError(f"Verification code '{entered_code}' is invalid")


class Session(Aggregate[UUID, Any]):
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
        self.created_at = created_at
        self.expires_at = expires_at
        self.closed_at = closed_at
        self.user_id = user_id

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
        return self.expires_at >= now and self.closed_at is None

    def close(self, now: datetime) -> None:
        if not self.is_active_now(now):
            raise DomainError("Can't close closed session")

        self.closed_at = now


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class User(Aggregate[UUID, Any]):
    def __init__(
        self,
        user_id: UUID,
        email: Email,
        role_id: UUID,
        first_name: str,
        last_name: str,
        status: UserStatus,
        password_hash: str,
        password_changed_at: datetime,
        created_by: UUID | None,
        email_verified_at: datetime | None,
        created_at: datetime,
    ) -> None:
        super().__init__(user_id)
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role_id = role_id
        self.status = status
        self.created_by = created_by
        self.password_hash = password_hash
        self.password_changed_at = password_changed_at
        self.email_verified_at = email_verified_at
        self.created_at = created_at

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def password_changed(self) -> bool:
        return self.password_changed_at is not None

    def verify_email(self, now: datetime) -> None:
        self.email_verified_at = now
        # Активируем пользователя после верификации email
        self.status = UserStatus.ACTIVE

    def change_password(
        self,
        service: PasswordService,
        old_password: UserPassword,
        new_password: UserPassword,
        now: datetime,
    ) -> None:
        if not service.verify(old_password, self.password_hash):
            raise DomainError("Old password is invalid")

        self.password_hash = service.hash_password(new_password)
        self.password_changed_at = now

    @classmethod
    def new(
        cls,
        user_id: UUID,
        email: Email,
        role_id: UUID,
        first_name: str,
        last_name: str,
        password_hash: str,
        created_by: UUID | None,
        now: datetime,
    ) -> "User":
        user = User(
            user_id=user_id,
            email=email,
            role_id=role_id,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            password_changed_at=now,
            created_by=created_by,
            email_verified_at=None,
            created_at=now,
            status=UserStatus.PENDING,
        )

        user._push_event(
            UserCreatedEvent(
                user_id=user_id,
                email=email.value,
                role_id=role_id,
                first_name=first_name,
                last_name=last_name,
            )
        )

        return user
