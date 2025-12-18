from datetime import datetime
from uuid import UUID

import pytest

from feedback.domain.user import User
from feedback.domain.value_objects import Email, UserPassword
from feedback.services.password_hasher import BcryptPasswordHasher


@pytest.fixture(scope="function")
async def viewer() -> User:
    return User.create_viewer(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        email=Email("johndoe@example.com"),
        first_name="John",
        last_name="Doe",
        password=UserPassword("Abacaba!23"),
        hasher=BcryptPasswordHasher(),
        created_at=datetime(2025, 10, 1),
    )


def test__viewer__can_activate_with_email_confirmation_without_password_change(
    viewer: User,
) -> None: ...
