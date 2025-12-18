from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from payments.domain.payment import PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=1, max_length=8)
    description: str | None = Field(default=None, max_length=512)
    expires_at: datetime


class PaymentResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    description: str | None
    expires_at: datetime
    created_at: datetime
    succeeded_at: datetime | None
    expired_at: datetime | None
