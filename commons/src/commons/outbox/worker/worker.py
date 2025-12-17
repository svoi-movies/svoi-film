import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from ..entity import Message

logger = logging.getLogger(__name__)


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
    async def publish(self, message: Message) -> None: ...


class Worker:

    def __init__(self, fetcher: Fetcher, publisher: Publisher) -> None:
        self._fetcher = fetcher
        self._publisher = publisher
        self._stopped = False

    async def run(self) -> None:
        while not self._stopped:
            sucess_messages: list[Message] = []
            failed_messages: list[Message] = []
            batch: list[Message] = []
            try:
                batch = await self._fetcher.fetch_messages_batch()

                if len(batch) > 0:
                    logger.info(f"Selected non-empty batch with len={len(batch)}")

                for message in batch:
                    try:
                        await self._publisher.publish(message)
                        sucess_messages.append(message)
                    except Exception as e:
                        failed_messages.append(message)
                        logger.error("Failed to send message", exc_info=e)

                    await self._fetcher.mark_messages_sent(sucess_messages)
                    await self._fetcher.mark_messages_for_retry(failed_messages)
            except Exception as e:
                all_ids = {m.id for m in batch}
                success_ids = {m.id for m in sucess_messages}
                all_failed_ids = all_ids - success_ids
                msgs_for_retry = [m for m in batch if m.id in all_failed_ids]
                await self._fetcher.mark_messages_for_retry(msgs_for_retry)
                logger.error("Unexpected error during woker cycle", exc_info=e)
            if failed_messages:
                logger.info(
                    f"From batch with len {len(batch)} {len(failed_messages)} failed to send"
                )

    def stop(self) -> None:
        self._stopped = True
