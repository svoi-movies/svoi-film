from uuid import UUID

from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage
from pydantic import BaseModel

from payments.use_cases.interfaces import PaymentUnitOfWork

broker = RabbitBroker()


class PaymentEvent(BaseModel):
    payment_id: UUID
    event: str


@broker.subscriber(
    queue="payments.debug",
    exchange="payments",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_payment_event(
    msg: RabbitMessage,
    body: PaymentEvent,
    uow: FromDishka[PaymentUnitOfWork],
) -> None:
    async with uow:
        print(f"Received payment event {body.event} for {body.payment_id} via {msg.routing_key}")
