from abc import ABC, abstractmethod
from typing import Any


class UnitOfWork[TEvent: Any](ABC):

    @abstractmethod
    async def __aenter__(self) -> None: ...

    @abstractmethod
    async def __aexit__(self, exc_type, val, tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def handle_domain_events(self, events: list[TEvent]) -> None: ...
