import aio_pika
from aio_pika.abc import AbstractConnection
from commons.auth.guards import AuthConfig, TokenService
from commons.auth.service import JwtTokenService
from commons.unit_of_work.dishka import DbConfig, SqlAlchemyProvider
from commons.utils.common_providers import DateTimeProvider, UUIDProvider
from commons.utils.dishka import CommonProvidersProvider
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from auth.config import Config
from auth.domain.role import PasswordService
from auth.domain.service import UserService
from auth.persistence.uow import UserUnitOfWork
from auth.services.jwt_issuer import JoseJwtIssuer
from auth.services.password_hasher import BcryptPasswordHasher
from auth.services.verification_code_generator import VerificationCodeGenerator
from auth.use_cases import interfaces
from auth.use_cases.commands import UserCommands
from auth.use_cases.queries import UserQueries


class AppProvider(Provider):
    # Скоуп по умолчанию
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    async def config(self) -> Config:
        return Config()  # pyright: ignore[reportCallIssue]

    @provide(scope=Scope.APP)
    async def db_config(self, config: Config) -> DbConfig:
        return config.db

    @provide(scope=Scope.REQUEST)
    def jwt_token_service(self, config: Config) -> TokenService:
        return JwtTokenService(
            config.jwt.verifying_key.get_secret_value(),
            algorithm="ES256",
        )

    @provide(scope=Scope.APP)
    async def auth_config(self, config: Config) -> AuthConfig:
        return config.auth

    @provide(scope=Scope.APP)
    async def rabbit_connection(self, config: Config) -> AbstractConnection:
        return await aio_pika.connect_robust(config.rabbit.dsn.encoded_string())

    @provide(scope=Scope.REQUEST)
    def jwt_issuer(
        self, config: Config, dt_provider: DateTimeProvider
    ) -> interfaces.JwtIssuer:
        return JoseJwtIssuer(
            signing_key=config.jwt.signing_key.get_secret_value(),
            access_token_ttl=config.jwt.access_token_ttl,
            refresh_token_ttl=config.jwt.refresh_token_ttl,
            date_time_provider=dt_provider,
        )

    @provide
    async def password_hasher(self) -> PasswordService:
        return BcryptPasswordHasher()

    @provide
    def verification_code_generator(self) -> VerificationCodeGenerator:
        return VerificationCodeGenerator()

    @provide
    def user_service(
        self,
        dt_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        password_service: PasswordService,
    ) -> UserService:
        return UserService(dt_provider, uuid_provider, password_service)

    # Запрашивается provides, возвращется source
    uow = provide(UserUnitOfWork, provides=interfaces.UserUnitOfWork)

    # source = provides
    commands = provide(UserCommands)
    queries = provide(UserQueries)

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        from auth.worker.handlers import broker

        main_broker = RabbitBroker(config.rabbit.dsn.encoded_string())
        main_broker.include_router(broker)
        return main_broker


def create_container() -> AsyncContainer:

    return make_async_container(
        # добавляет AsyncEngine и AsyncSession
        SqlAlchemyProvider(),
        # добавляет DateTimeProvider и UUIDProvider
        CommonProvidersProvider(scope=Scope.REQUEST),
        AppProvider(),
    )
