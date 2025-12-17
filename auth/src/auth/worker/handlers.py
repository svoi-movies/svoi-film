from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage
from pydantic import BaseModel

from auth.use_cases.interfaces import UserUnitOfWork

broker = RabbitBroker()


class Sum(BaseModel):
    a: int
    b: int


class SumResult(BaseModel):
    result: int


@broker.subscriber(
    queue="test",
    exchange="direct.test",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
@broker.publisher(
    exchange="direct.test.results",
)
async def test_worker(
    msg: RabbitMessage, body: Sum, uow: FromDishka[UserUnitOfWork]
) -> SumResult:
    print(body)
    return SumResult(result=body.a + body.b)
