from typing import Literal

import bcrypt

from auth.domain.value_objects import UserPassword


class BcryptPasswordHasher:
    def __init__(
        self,
        encoding: str = "utf-8",
        salt_rounds: int = 12,
        salt_prefix: Literal[b"2a", b"2b"] = b"2b",
    ) -> None:
        self.encoding = encoding
        self.salt_rounds = salt_rounds
        self.salt_prefix = salt_prefix

    def hash_password(self, password: UserPassword) -> str:
        return bcrypt.hashpw(
            password.value.encode(self.encoding),
            salt=bcrypt.gensalt(
                rounds=self.salt_rounds,
                prefix=self.salt_prefix,
            ),
        ).hex()

    def verify(self, password: UserPassword, password_hash: str) -> bool:
        return bcrypt.checkpw(
            password=password.value.encode(self.encoding),
            hashed_password=bytes.fromhex(password_hash),
        )
