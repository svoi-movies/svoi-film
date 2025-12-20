import aio_pika
from aio_pika.abc import AbstractConnection
from commons.unit_of_work.dishka import DbConfig, SqlAlchemyProvider
from commons.utils.dishka import CommonProvidersProvider
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from streaming.config import Config, S3Config
from streaming.events import EventPublisher
from streaming.persistence.uow import StreamingUnitOfWork
from streaming.services import S3Service
from streaming.use_cases import ViewerCommands, TitleCommands, SessionCommands


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

    @provide(scope=Scope.APP)
    async def s3_config(self, config: Config) -> S3Config:
        return config.s3

    # Dishka wiring
    s3_service = provide(S3Service, scope=Scope.APP)
    event_publisher = provide(EventPublisher, scope=Scope.APP)
    uow = provide(StreamingUnitOfWork)
    viewer_commands = provide(ViewerCommands)
    title_commands = provide(TitleCommands)
    session_commands = provide(SessionCommands)

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        main_broker = RabbitBroker(config.rabbit.dsn.encoded_string())
        return main_broker


def create_container() -> AsyncContainer:
    return make_async_container(
        SqlAlchemyProvider(),
        CommonProvidersProvider(scope=Scope.REQUEST),
        AppProvider(),
    )
