from uuid import UUID

from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange
from pydantic import BaseModel

from feedback.use_cases.commands import FeedbackCommands

broker = RabbitBroker()

titles_exchange = RabbitExchange("ikbo0722.titles", type=ExchangeType.TOPIC, durable=True)


class TitleCreatedEvent(BaseModel):
    title_id: UUID


class TitleDeletedEvent(BaseModel):
    title_id: UUID


@broker.subscriber(
    "ikbo0722.titles.created",
    exchange=titles_exchange,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def handle_title_created(
    body: TitleCreatedEvent,
    commands: FromDishka[FeedbackCommands],
) -> None:
    await commands.add_title(body.title_id)


@broker.subscriber(
    "ikbo0722.titles.deleted",
    exchange=titles_exchange,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def handle_title_deleted(
    body: TitleDeletedEvent,
    commands: FromDishka[FeedbackCommands],
) -> None:
    await commands.delete_title(body.title_id)
