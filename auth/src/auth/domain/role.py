from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol, override
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError

from auth.domain.value_objects import Email, UserPassword


class PasswordService(Protocol):

    def hash_password(self, password: UserPassword) -> str: ...

    def verify(self, password: UserPassword, password_hash: str) -> bool: ...


class CreationAction: ...


class SendEmailVerificationCodeAction(CreationAction): ...


class SendEmailOneTimePassword(CreationAction): ...


class ActivationRequirements(ABC):
    type: str

    @abstractmethod
    def check(self, user: "User") -> bool: ...


class MustVerifyEmail(ActivationRequirements):

    @override
    def check(self, user: "User") -> bool:
        return user.email_verified


class MustChangePassword(ActivationRequirements):

    @override
    def check(self, user: "User") -> bool:
        return user.password_changed


class Role(Aggregate[UUID, Any]):

    def __init__(
        self,
        role_id: UUID,
        name: str,
        creation_actions: list[CreationAction],
        activation_requirements: list[ActivationRequirements],
        allow_self_registration: bool,
    ) -> None:
        super().__init__(role_id)
        self._name = name
        self._activation_requirements = activation_requirements
        self._creation_actions = creation_actions
        self._allow_self_registration = allow_self_registration

    @property
    def name(self) -> str:
        return self._name

    @property
    def activation_requirements(self) -> list[ActivationRequirements]:
        return self._activation_requirements[:]

    @property
    def creation_actions(self) -> list[CreationAction]:
        return self._creation_actions[:]

    @property
    def allow_self_registration(self) -> bool:
        return self._allow_self_registration


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
        self._user_id = user_id
        self._code = code
        self._valid_until = valid_until
        self._created_at = created_at

        with Validator() as v:
            v.must_regexp_full_match(
                r"\d\d\d-\d\d\d",
                self._code,
                "Verification code must match the pattern 000-000",
            )
            v.must(
                lambda: self._valid_until > self._created_at,
                "Valid until must be greater than creation time",
            )

    def verify(self, entered_code: str, now: datetime) -> None:
        if now >= self._valid_until:
            raise DomainError("Verification code has expired")

        if not self._code == entered_code:
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
        self._email = email
        self._first_name = first_name
        self._last_name = last_name
        self._role_id = role_id
        self._status = status
        self._created_by = created_by
        self._password_hash = password_hash
        self._password_changed_at = password_changed_at
        self._email_verified_at = email_verified_at
        self._created_at = created_at

    def activate(self) -> None:
        self._status = UserStatus.ACTIVE

    @property
    def role_id(self) -> UUID:
        return self._role_id

    def verify_email(self, now: datetime) -> None:
        self._email_verified_at = now
        self._push_event(EmailVerifiedEvent(self.id, self._email.value, now))

    def change_password(
        self,
        service: PasswordService,
        old_password: UserPassword,
        new_password: UserPassword,
        now: datetime,
    ) -> None:
        if not service.verify(old_password, self._password_hash):
            raise DomainError("Old password is invalid")

        self._password_hash = service.hash_password(new_password)
        self._password_changed_at = now
        self._push_event(PasswordChangedEvent(self.id, self._email.value, now))

    @property
    def email_verified(self) -> bool:
        return self._email_verified_at is not None

    @property
    def password_changed(self) -> bool:
        return self._password_changed_at is not None

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def email(self) -> Email:
        return self._email

    @property
    def password_hash(self) -> str:
        return self._password_hash

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
        return User(
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


@dataclass(slots=True, frozen=True, eq=True)
class EmailVerifiedEvent:
    user_id: UUID
    email: str
    verified_at: datetime


@dataclass(slots=True, frozen=True, eq=True)
class PasswordChangedEvent:
    user_id: UUID
    email: str
    changed_at: datetime
