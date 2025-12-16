from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from commons.ddd import Validator
from pytz import UTC


def is_in_utc(dt: datetime) -> Callable[[], bool]:
    return lambda: dt.tzinfo == UTC


@dataclass(frozen=True, eq=True, slots=True)
class UserPassword:
    value: str

    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 32
    ANY_LETTER = r"[a-zA-Z]"
    ANY_DIGIT = r"[a-zA-Z]"
    ANY_SPECIAL = r"[^\s\da-zA-Z]"

    def __post_init__(self) -> None:
        with Validator() as v:
            v.must(
                lambda: len(self.value) >= self.MIN_PASSWORD_LENGTH,
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters length",
            )

            v.must(
                lambda: len(self.value) <= self.MAX_PASSWORD_LENGTH,
                f"password must be not greater than {self.MAX_PASSWORD_LENGTH} characters length",
            )

            v.must_regexp_match(
                self.ANY_LETTER,
                self.value,
                "Password must contain any letter",
            )

            v.must_regexp_match(
                self.ANY_LETTER,
                self.value,
                "Password must contain any digit",
            )

            v.must_regexp_match(
                self.ANY_SPECIAL,
                self.value,
                "Password must contain any special symbol",
            )


@dataclass(frozen=True, slots=True, eq=True)
class ActivationCode:
    code: str
    valid_until: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        with Validator() as v:
            v.must_regexp_full_match(
                r"\d\d\d-\d\d\d",
                self.code,
                "Activation code must match the pattern 000-000",
            )
            v.must(
                lambda: self.valid_until > self.created_at,
                "Valid until must be greater than creation time",
            )

            v.must(is_in_utc(self.valid_until), "Valid until must has any timezone")
            v.must(is_in_utc(self.created_at), "Created at must has any timezone")


@dataclass(frozen=True, slots=True, eq=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        with Validator() as v:
            v.must_regexp_full_match(
                r"[a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+",
                self.value,
                "Must be a valid email",
            )
