from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

"""
Тут лежат модельки для запросов и ответов
"""


# Так можно переиспользовать поля в разных типах, но конкретно тут излишне
type FirstName = Annotated[str, Field(min_length=1, max_length=32)]
type LastName = Annotated[str, Field(min_length=1, max_length=32)]
type Password = Annotated[str, Field(min_length=8, max_length=32)]


class SelfRegisterRequest(BaseModel):
    role: str
    email: EmailStr
    first_name: FirstName
    last_name: LastName
    password: Password


class SelfRegisterResponse(BaseModel):
    id: UUID


class UserRole(Enum):
    MODERATOR = "moderator"
    VIEWER = "viewer"
    CONTENT_OWNER = "content_owver"


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class GetMeResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    allow_self_registration: bool
    creator_role_id: UUID | None = None


class CreateRoleResponse(BaseModel):
    id: UUID


class RoleResponse(BaseModel):
    id: UUID
    name: str
    allow_self_registration: bool
    creator_role_id: UUID | None


class CreateUserRequest(BaseModel):
    role: str
    email: EmailStr
    first_name: FirstName
    last_name: LastName
    password: Password


class CreateUserResponse(BaseModel):
    id: UUID
