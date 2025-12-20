from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from streaming.domain.episode import EpisodeStatus


# Viewer models
class ViewerResponse(BaseModel):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None
    is_deleted: bool


# Title models
class CreateTitleRequest(BaseModel):
    name: str
    description: str | None = None
    director: str | None = None


class TitleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    director: str | None
    created_at: datetime


# Episode models
class CreateEpisodeRequest(BaseModel):
    title_id: UUID
    name: str
    description: str | None = None
    duration: int | None = None


class CreateEpisodeResponse(BaseModel):
    episode: "EpisodeResponse"
    upload_url: str


class EpisodeResponse(BaseModel):
    id: UUID
    title_id: UUID
    s3_key: str
    name: str
    description: str | None
    duration: int | None
    status: EpisodeStatus
    created_at: datetime
    uploaded_at: datetime | None
    processed_at: datetime | None
    published_at: datetime | None
    hidden_at: datetime | None


# Viewing Session models
class CreateSessionRequest(BaseModel):
    viewer_id: UUID
    episode_id: UUID


class UpdateProgressRequest(BaseModel):
    progress_seconds: int = Field(ge=0)


class ViewingSessionResponse(BaseModel):
    id: UUID
    viewer_id: UUID
    episode_id: UUID
    progress_seconds: int
    created_at: datetime
    completed_at: datetime | None
    is_completed: bool


class GetStreamingUrlRequest(BaseModel):
    viewer_id: UUID
    episode_id: UUID


class StreamingUrlResponse(BaseModel):
    streaming_url: str
