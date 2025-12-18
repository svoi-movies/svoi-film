from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class MessageStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    SENT = "SENT"


@dataclass
class Message:
    id: UUID
    job_id: str | None
    status: MessageStatus
    destination_topic: str
    routing_key: str
    message: str
    tries: int
    process_started_at: datetime | None
    process_done_at: datetime | None
    created_at: datetime
    rowversion: int
    process_timeout_ms: int | None
