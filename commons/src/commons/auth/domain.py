from enum import Enum
from typing import Annotated, Sequence
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Role(Enum):
    MODERATOR = "moderator"
    VIEWER = "viewer"
    CONTENT_OWNER = "content_owner"
    ADMIN = "admin"


class UserClaims(BaseModel):
    user_id: Annotated[UUID, Field(alias="sub")]
    session_id: Annotated[UUID, Field(alias="sid")]
    email: EmailStr
    first_name: str
    last_name: str
    role: Role


def can_access_with_roles(
    user_role: Role,
    allowed_roles: Sequence[Role] | None,
) -> bool:
    if not allowed_roles:
        return True

    if user_role == Role.ADMIN:
        return True

    return user_role in allowed_roles
