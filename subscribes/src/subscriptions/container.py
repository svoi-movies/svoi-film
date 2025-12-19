import aio_pika
from aio_pika.abc import AbstractConnection
from commons.unit_of_work.dishka import DbConfig, SqlAlchemyProvider
from commons.utils.dishka import CommonProvidersProvider
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from subscriptions.config import Config
from subscriptions.persistence.uow import SubscriptionUnitOfWork
from subscriptions.use_cases import interfaces
from subscriptions.use_cases.commands import SubscriptionCommands
from subscriptions.use_cases.queries import SubscriptionQueries


class AppProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    async def config(self) -> Config:
        return Config()  # pyright: ignore[reportCallIssue]

    @provide(scope=Scope.APP)
    async def db_config(self, config: Config) -> DbConfig:
        return config.db

    @provide(scope=Scope.APP)
    async def rabbit_connection(self, config: Config) -> AbstractConnection:
        return await aio_pika.connect_robust(config.rabbit.dsn.encoded_string())

    # Dishka wiring
    uow = provide(SubscriptionUnitOfWork, provides=interfaces.SubscriptionUnitOfWork)
    commands = provide(SubscriptionCommands)
    queries = provide(SubscriptionQueries)

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        from subscriptions.worker.handlers import broker

        main_broker = RabbitBroker(config.rabbit.dsn.encoded_string())
        main_broker.include_router(broker)
        return main_broker


def create_container() -> AsyncContainer:
    return make_async_container(
        SqlAlchemyProvider(),
        CommonProvidersProvider(scope=Scope.REQUEST),
        AppProvider(),
    )
