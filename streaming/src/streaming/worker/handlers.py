from uuid import UUID

from dishka.integrations.faststream import FromDishka
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage
from pydantic import BaseModel

from streaming.use_cases import TitleCommands

broker = RabbitBroker()


class EpisodeSourceUploadedEvent(BaseModel):
    episode_id: UUID
    uploaded_at: str


@broker.subscriber(
    queue="streaming.video_processing",
    exchange="streaming",
    routing_key="episode.source_uploaded",
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def process_video(
    msg: RabbitMessage,
    body: EpisodeSourceUploadedEvent,
    commands: FromDishka[TitleCommands],
) -> None:
    print(f"Processing video for episode {body.episode_id}")

    # Simulate video processing
    # In real implementation: transcode video, generate different quality versions, extract metadata, etc.
    await commands.process_episode_source(body.episode_id)

    print(f"Video processing completed for episode {body.episode_id}")
