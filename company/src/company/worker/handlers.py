from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage

broker = RabbitBroker()


@broker.subscriber(
    queue="company.debug",
    exchange="company",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_company_event(msg: RabbitMessage) -> None:
    print(
        f"Received company event via {msg.routing_key}: {msg.body.decode()}"
    )


@broker.subscriber(
    queue="content-owner.debug",
    exchange="content-owner",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_content_owner_event(msg: RabbitMessage) -> None:
    print(
        f"Received content-owner event via {msg.routing_key}: {msg.body.decode()}"
    )
