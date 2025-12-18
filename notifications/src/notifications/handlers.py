from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel, EmailStr

from notifications.use_cases import NotificationCommands

broker = RabbitBroker()


class SendNotificationRequest(BaseModel):
    subject: str
    body: str
    email: EmailStr


@broker.subscriber(
    queue="ikbo0722.burenin.notifications",
    exchange="ikbo0722.burenin.notifications",
    ack_policy=AckPolicy.REJECT_ON_ERROR,
)
async def send_notification(
    req: SendNotificationRequest,
    commands: FromDishka[NotificationCommands],
) -> None:
    await commands.send_email_notification(req.email, req.subject, req.body)
