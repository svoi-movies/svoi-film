import aio_pika
from aio_pika.abc import AbstractConnection
from commons.auth.guards import AuthConfig, TokenService
from commons.auth.service import JwtTokenService
from commons.unit_of_work.dishka import DbConfig, SqlAlchemyProvider
from commons.utils.dishka import CommonProvidersProvider
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from feedback.config import Config
from feedback.persistence.uow import FeedbackUnitOfWork
from feedback.use_cases import interfaces
from feedback.use_cases.commands import FeedbackCommands
from feedback.use_cases.queries import FeedbackQueries


class AppProvider(Provider):
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

    uow = provide(FeedbackUnitOfWork, provides=interfaces.FeedbackUnitOfWork)

    commands = provide(FeedbackCommands)
    queries = provide(FeedbackQueries)

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        from feedback.worker.handlers import broker

        main_broker = RabbitBroker(config.rabbit.dsn.encoded_string())
        main_broker.include_router(broker)
        return main_broker


def create_container() -> AsyncContainer:
    return make_async_container(
        SqlAlchemyProvider(),
        CommonProvidersProvider(scope=Scope.REQUEST),
        AppProvider(),
    )
