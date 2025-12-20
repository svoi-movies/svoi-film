from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from moderator.domain import ModerationRequestStatus, ModeratorStatus


class AuthUserPayload(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)


class CreateModeratorRequest(BaseModel):
    user: AuthUserPayload


class CreateModerationRequest(BaseModel):
    episode_id: UUID
    content_owner_id: UUID


class ResolveModerationRequest(BaseModel):
    moderator_id: UUID


class ModeratorResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: ModeratorStatus
    created_at: datetime
    updated_at: datetime


class ModerationRequestResponse(BaseModel):
    id: UUID
    episode_id: UUID
    content_owner_id: UUID
    moderator_id: UUID | None
    status: ModerationRequestStatus
    created_at: datetime
    updated_at: datetime
