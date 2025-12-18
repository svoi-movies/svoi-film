from dataclasses import dataclass

from commons.ddd import Validator


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
class Email:
    value: str

    def __post_init__(self) -> None:
        with Validator() as v:
            v.must_regexp_full_match(
                r"[a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+",
                self.value,
                "Must be a valid email",
            )
