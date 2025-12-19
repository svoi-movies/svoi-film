from typing import Any, override

from commons.outbox.sqlalchemy import DataclassSerializer, OutboxRepository
from commons.unit_of_work.sqlalchemy import UnitOfWork
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.role import UserCreatedEvent
from auth.persistence.role_repository import SqlAlchemyRoleRepository
from auth.persistence.session_repository import SqlAlchemySessionRepository
from auth.persistence.user_repository import SqlAlchemyUserRepository
from auth.persistence.verification_code_repository import (
    SqlAlchemyVerificationCodeRepository,
)
from auth.use_cases import interfaces


class UserUnitOfWork(interfaces.UserUnitOfWork, UnitOfWork[Any]):
    """
    В целом вся логика уже реализована в commons.unit_of_work,
    так что этот класс чисто инициализирует репозитории
    и хендлит доменные ивенты (перекладывает в аутбокс)
    """

    def __init__(
        self,
        session: AsyncSession,
        uuid_provider: UUIDProvider,
        dt_provider: DateTimeProvider,
    ) -> None:
        super().__init__(session)
        self._outbox_repository = OutboxRepository(
            session, serializer=DataclassSerializer()
        )
        self._uuid_provider = uuid_provider
        self._dt_provider = dt_provider
        self._users = SqlAlchemyUserRepository(session)
        self._sessions = SqlAlchemySessionRepository(session)
        self._roles = SqlAlchemyRoleRepository(session)
        self._verification_codes = SqlAlchemyVerificationCodeRepository(session)

    @property
    def users(self) -> interfaces.UserRepository:
        return self._users

    @property
    def sessions(self) -> interfaces.SessionRepository:
        return self._sessions

    @property
    def roles(self) -> interfaces.RoleRepository:
        return self._roles

    @property
    def verification_codes(self) -> interfaces.VerificationCodeReposiory:
        return self._verification_codes

    @override
    async def handle_domain_events(self, events: list[Any]) -> None:
        for event in events:
            destination_topic = "ikbo0722.burenin.users"
            if isinstance(event, UserCreatedEvent):
                routing_key = "ikbo0722.burenin.users.created"
            else:
                raise TypeError(f"Can't handle message of type {type(event)}: {event}")

            self._outbox_repository.add(
                message_id=self._uuid_provider.new_v4(),
                created_at=self._dt_provider.now_utc,
                destination_topic=destination_topic,
                routing_key=routing_key,
                message=event,
            )
