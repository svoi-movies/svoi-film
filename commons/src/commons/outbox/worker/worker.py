import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MessageStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    SENT = "done"


class Message(BaseModel):
    id: UUID
    status: MessageStatus
    destination_topic: str
    message: str
    tries: int
    max_tries: int
    created_at: datetime
    process_started_at: datetime | None
    process_done_at: datetime | None
    process_timeout: datetime | None
    rowversion: int


@dataclass
class MessageForPublish:
    id: UUID
    message: str


class Fetcher(ABC):

    @abstractmethod
    async def fetch_messages_batch(self) -> list[Message]: ...

    @abstractmethod
    async def mark_messages_for_retry(self, messages: list[Message]) -> None: ...

    @abstractmethod
    async def mark_messages_sent(self, messages: list[Message]) -> None: ...


class Publisher(ABC):

    @abstractmethod
    async def publish(self, topic: str, message: MessageForPublish) -> None: ...


class Worker:

    def __init__(self, fetcher: Fetcher, publisher: Publisher) -> None:
        self._fetcher = fetcher
        self._publisher = publisher
        self._stopped = False

    async def run(self) -> None:
        while not self._stopped:
            sucess_messages: list[Message] = []
            failed_messages: list[Message] = []
            try:
                batch = await self._fetcher.fetch_messages_batch()
                logger.info(f"Selected batch len={len(batch)}")
                for message in batch:
                    try:
                        await self._publisher.publish(
                            message.destination_topic,
                            MessageForPublish(message.id, message.message),
                        )
                        sucess_messages.append(message)
                    except Exception as e:
                        failed_messages.append(message)
                        logger.error("Failed to send message", exc_info=e)

                    await self._fetcher.mark_messages_sent(sucess_messages)
            except Exception as e:
                await self._fetcher.mark_messages_sent(failed_messages)
                logger.error("Unexpected error during woker cycle", exc_info=e)

    def stop(self) -> None:
        self._stopped = True
