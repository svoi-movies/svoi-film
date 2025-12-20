from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from subscriptions.domain.subscription import SubscriptionLevel, SubscriptionStatus


class CreateSubscriptionRequest(BaseModel):
    level: SubscriptionLevel
    expires_at: datetime


class RenewSubscriptionRequest(BaseModel):
    new_expires_at: datetime = Field(alias="expires_at")

    model_config = {"populate_by_name": True}


class RequestLevelChange(BaseModel):
    target_level: SubscriptionLevel


class SubscriptionResponse(BaseModel):
    id: UUID
    level: SubscriptionLevel
    status: SubscriptionStatus
    expires_at: datetime
    created_at: datetime
    cancelled_at: datetime | None
    pending_level: SubscriptionLevel | None
    level_change_initiated_at: datetime | None
