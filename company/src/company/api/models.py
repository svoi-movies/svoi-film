from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from company.domain import CompanyStatus, ContentOwnerStatus


class AuthUserPayload(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)


class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AddContentOwnerRequest(BaseModel):
    user: AuthUserPayload
    permissions: list[str] = Field(default_factory=list)


class CreateContentOwnerRequest(BaseModel):
    user: AuthUserPayload
    company_id: UUID
    permissions: list[str] = Field(default_factory=list)


class UpdateContentOwnerPermissionsRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class UpdatePermissionsRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    status: CompanyStatus
    created_at: datetime
    updated_at: datetime


class ContentOwnerResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    permissions: list[str]
    status: ContentOwnerStatus
    created_at: datetime
    updated_at: datetime
