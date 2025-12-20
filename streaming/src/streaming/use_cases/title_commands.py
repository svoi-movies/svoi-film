from datetime import datetime
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from streaming.domain.title import Title
from streaming.domain.episode import Episode
from streaming.events import EventPublisher
from streaming.persistence.uow import StreamingUnitOfWork
from streaming.services import S3Service


class TitleCommands:
    def __init__(
        self,
        uow: StreamingUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        s3_service: S3Service,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider
        self._s3_service = s3_service
        self._event_publisher = event_publisher

    async def create_title(
        self,
        name: str,
        description: str | None = None,
        director: str | None = None,
    ) -> Title:
        now = self._datetime_provider.now_utc
        title = Title.new(
            title_id=self._uuid_provider.new_v4(),
            name=name,
            description=description,
            director=director,
            now=now,
        )
        async with self._uow:
            self._uow.titles.add(title)
            await self._uow.commit()
        return title

    async def add_episode_draft(
        self,
        title_id: UUID,
        name: str,
        description: str | None = None,
        duration: int | None = None,
    ) -> tuple[Episode, str]:
        now = self._datetime_provider.now_utc
        episode_id = self._uuid_provider.new_v4()

        upload_url, s3_key = self._s3_service.generate_upload_presigned_url(episode_id)

        episode = Episode.new(
            episode_id=episode_id,
            title_id=title_id,
            s3_key=s3_key,
            name=name,
            description=description,
            duration=duration,
            now=now,
        )
        async with self._uow:
            # Verify title exists
            await self._uow.titles.get_by_id(title_id)
            self._uow.episodes.add(episode)
            await self._uow.commit()
        return episode, upload_url

    async def upload_episode_source(self, episode_id: UUID) -> Episode:
        now = self._datetime_provider.now_utc
        async with self._uow:
            episode = await self._uow.episodes.get_by_id(episode_id)
            episode.upload_source(now)
            await self._uow.commit()

            # Publish event to trigger video processing
            await self._event_publisher.publish(
                routing_key="episode.source_uploaded",
                event={
                    "episode_id": str(episode_id),
                    "uploaded_at": now.isoformat(),
                },
            )

            return episode

    async def process_episode_source(self, episode_id: UUID) -> Episode:
        now = self._datetime_provider.now_utc
        async with self._uow:
            episode = await self._uow.episodes.get_by_id(episode_id)
            episode.process_source(now)
            await self._uow.commit()
            return episode

    async def publish_episode(self, episode_id: UUID) -> Episode:
        now = self._datetime_provider.now_utc
        async with self._uow:
            episode = await self._uow.episodes.get_by_id(episode_id)
            episode.publish(now)
            await self._uow.commit()
            return episode

    async def hide_episode(self, episode_id: UUID) -> Episode:
        now = self._datetime_provider.now_utc
        async with self._uow:
            episode = await self._uow.episodes.get_by_id(episode_id)
            episode.hide(now)
            await self._uow.commit()
            return episode
