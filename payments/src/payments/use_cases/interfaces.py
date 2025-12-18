from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from payments.domain import Payment


class PaymentRepository(Protocol):

    def add(self, payment: Payment) -> None: ...

    async def save(self, payment: Payment) -> None: ...

    async def get_by_id(self, payment_id: UUID) -> Payment: ...


class PaymentUnitOfWork(ABC):
    @property
    @abstractmethod
    def payments(self) -> PaymentRepository: ...

    @abstractmethod
    async def __aenter__(self) -> None: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
