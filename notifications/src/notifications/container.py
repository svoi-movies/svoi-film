from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker

from notifications.config import Config
from notifications.service import EmailService
from notifications.use_cases import NotificationCommands


class AppProvider(Provider):
    # Скоуп по умолчанию
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    async def config(self) -> Config:
        return Config()  # pyright: ignore[reportCallIssue]

    @provide(scope=Scope.APP)
    def rabbit(self, config: Config) -> RabbitBroker:
        from notifications.handlers import broker

        main_broker = RabbitBroker(config.rabbit_dsn.encoded_string())
        main_broker.include_router(broker)
        return main_broker

    @provide(scope=Scope.APP)
    def smtp_service(self, config: Config) -> EmailService:
        return EmailService(
            smtp_host=config.smtp.host,
            smtp_port=config.smtp.port,
            smtp_user=config.smtp.user,
            smtp_password=config.smtp.password,
        )

    commands = provide(NotificationCommands)


def create_container() -> AsyncContainer:
    return make_async_container(
        # добавляет DateTimeProvider и UUIDProvider
        AppProvider(),
    )
