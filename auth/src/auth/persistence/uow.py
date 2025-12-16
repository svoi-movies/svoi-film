from typing import Any

from commons.outbox.sqlalchemy.repository import OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from auth.persistence.user_repository import SqlAlchemyUserRepository
from auth.use_cases import interfaces


class UserUnitOfWork(interfaces.UserUnitOfWork, UnitOfWork[Any]):
    """
    В целом вся логика уже реализована в commons.unit_of_work,
    так что этот класс чисто инициализирует репозитории
    и хендлит доменные ивенты (перекладывает в аутбокс)
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self._outbox_repository = OutboxRepository(session)
        self._users = SqlAlchemyUserRepository(session)

    async def handle_domain_events(self, events: list[Any]) -> None: ...

    @property
    def users(self) -> interfaces.UserRepository:
        return self._users
