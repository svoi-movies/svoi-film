from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage

broker = RabbitBroker()


@broker.subscriber(
    queue="moderator.debug",
    exchange="moderator",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_moderator_event(msg: RabbitMessage) -> None:
    print(
        f"Received moderator event via {msg.routing_key}: {msg.body.decode()}"
    )


@broker.subscriber(
    queue="moderation-request.debug",
    exchange="moderation-request",
    routing_key="#",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def log_moderation_request_event(msg: RabbitMessage) -> None:
    print(
        f"Received moderation-request event via {msg.routing_key}: {msg.body.decode()}"
    )
