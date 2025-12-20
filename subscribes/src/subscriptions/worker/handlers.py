from uuid import UUID

from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage
from pydantic import BaseModel

from subscriptions.use_cases.interfaces import SubscriptionUnitOfWork

broker = RabbitBroker()


class SubscriptionEvent(BaseModel):
    subscription_id: UUID
    event: str


@broker.subscriber(
    queue="subscriptions.debug",
    exchange="subscriptions",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_subscription_event(
    msg: RabbitMessage,
    body: SubscriptionEvent,
    uow: FromDishka[SubscriptionUnitOfWork],
) -> None:
    async with uow:
        print(
            f"Received subscription event {body.event} for {body.subscription_id} via {msg.routing_key}"
        )
