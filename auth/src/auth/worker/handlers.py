from uuid import UUID

from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel

from auth.use_cases.commands import UserCommands

broker = RabbitBroker()


class UserCreatedEvent(BaseModel):
    user_id: UUID
    email: str
    role_id: UUID
    first_name: str
    last_name: str


class EmailNotification(BaseModel):
    subject: str
    body: str
    email: str


@broker.subscriber(
    queue="auth.user_created",
    exchange="ikbo0722.burenin.users",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
@broker.publisher(
    exchange="ikbo0722.burenin.notifications",
)
async def send_verification_code(
    event: UserCreatedEvent,
    commands: FromDishka[UserCommands],
) -> EmailNotification:
    """Обрабатывает событие создания пользователя и отправляет код верификации на email"""

    # Создаем код верификации через use case
    verification_code = await commands.create_verification_code(event.user_id)

    # Формируем сообщение для отправки
    return EmailNotification(
        subject="Код верификации для входа",
        body=f"Здравствуйте, {event.first_name}!\n\n"
             f"Ваш код верификации: {verification_code.code}\n\n"
             f"Код действителен в течение 24 часов.",
        email=event.email,
    )
