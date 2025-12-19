from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from subscriptions.domain import Subscription


class SubscriptionRepository(Protocol):

    def add(self, subscription: Subscription) -> None: ...

    async def save(self, subscription: Subscription) -> None: ...

    async def get_by_id(self, subscription_id: UUID) -> Subscription: ...


class SubscriptionUnitOfWork(ABC):
    @property
    @abstractmethod
    def subscriptions(self) -> SubscriptionRepository: ...

    @abstractmethod
    async def __aenter__(self) -> None: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
