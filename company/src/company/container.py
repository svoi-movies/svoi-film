import aio_pika
from aio_pika.abc import AbstractConnection
from commons.auth.guards import AuthConfig, TokenService
from commons.auth.service import JwtTokenService
from commons.unit_of_work.dishka import DbConfig, SqlAlchemyProvider
from commons.utils.dishka import CommonProvidersProvider
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from company.config import AuthClientConfig, Config, JwtConfig
from company.persistence.uow import CompanyUnitOfWork
from company.use_cases import interfaces
from company.use_cases.auth_service import HttpxAuthService
from company.use_cases.commands import CompanyCommands
from company.use_cases.queries import CompanyQueries


class AppProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    async def config(self) -> Config:
        return Config()  # pyright: ignore[reportCallIssue]

    @provide(scope=Scope.APP)
    async def db_config(self, config: Config) -> DbConfig:
        return config.db

    @provide(scope=Scope.APP)
    async def auth_config(self, config: Config) -> AuthConfig:
        return config.auth

    @provide(scope=Scope.APP)
    async def auth_client_config(self, config: Config) -> AuthClientConfig:
        return config.auth_client

    @provide(scope=Scope.REQUEST)
    def jwt_token_service(self, config: Config) -> TokenService:
        jwt_cfg: JwtConfig = config.jwt
        return JwtTokenService(
            jwt_cfg.verifying_key.get_secret_value(),
            algorithm="ES256",
        )

    @provide(scope=Scope.APP)
    async def rabbit_connection(self, config: Config) -> AbstractConnection:
        return await aio_pika.connect_robust(config.rabbit.dsn.encoded_string())

    # Dishka wiring
    uow = provide(CompanyUnitOfWork, provides=interfaces.CompanyUnitOfWork)
    auth_service = provide(HttpxAuthService, provides=interfaces.AuthService)
    commands = provide(CompanyCommands)
    queries = provide(CompanyQueries)

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        from company.worker.handlers import broker

        main_broker = RabbitBroker(config.rabbit.dsn.encoded_string())
        main_broker.include_router(broker)
        return main_broker


def create_container() -> AsyncContainer:
    return make_async_container(
        SqlAlchemyProvider(),
        CommonProvidersProvider(scope=Scope.REQUEST),
        AppProvider(),
    )
