from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from content_owner.domain.content_owner import ContentOwnerStatus


class AuthUserPayload(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)


class CreateContentOwnerRequest(BaseModel):
    user: AuthUserPayload
    company_id: UUID
    permissions: list[str] = Field(default_factory=list)


class UpdatePermissionsRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class ContentOwnerResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    permissions: list[str]
    status: ContentOwnerStatus
    created_at: datetime
    updated_at: datetime
