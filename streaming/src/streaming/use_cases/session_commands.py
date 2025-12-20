from datetime import datetime
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from commons.ddd.errors import DomainError

from streaming.domain.episode import EpisodeStatus
from streaming.domain.viewing_session import ViewingSession
from streaming.persistence.uow import StreamingUnitOfWork
from streaming.services import S3Service


class SessionCommands:
    def __init__(
        self,
        uow: StreamingUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        s3_service: S3Service,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider
        self._s3_service = s3_service

    async def create_session(
        self,
        viewer_id: UUID,
        episode_id: UUID,
    ) -> ViewingSession:
        now = self._datetime_provider.now_utc
        session = ViewingSession.new(
            session_id=self._uuid_provider.new_v4(),
            viewer_id=viewer_id,
            episode_id=episode_id,
            now=now,
        )
        async with self._uow:
            # Verify viewer and episode exist
            await self._uow.viewers.get_by_id(viewer_id)
            await self._uow.episodes.get_by_id(episode_id)
            self._uow.viewing_sessions.add(session)
            await self._uow.commit()
        return session

    async def update_progress(
        self,
        session_id: UUID,
        progress_seconds: int,
    ) -> ViewingSession:
        now = self._datetime_provider.now_utc
        async with self._uow:
            session = await self._uow.viewing_sessions.get_by_id(session_id)
            session.update_progress(progress_seconds, now)
            await self._uow.commit()
            return session

    async def complete_session(self, session_id: UUID) -> ViewingSession:
        now = self._datetime_provider.now_utc
        async with self._uow:
            session = await self._uow.viewing_sessions.get_by_id(session_id)
            session.complete(now)
            await self._uow.commit()
            return session

    async def get_streaming_url(
        self,
        viewer_id: UUID,
        episode_id: UUID,
    ) -> str:
        async with self._uow:
            # Verify viewer exists and is not deleted
            viewer = await self._uow.viewers.get_by_id(viewer_id)
            if viewer.is_deleted:
                raise DomainError("Viewer is deleted")

            # Verify episode exists and is published
            episode = await self._uow.episodes.get_by_id(episode_id)
            if episode.status != EpisodeStatus.PUBLISHED:
                raise DomainError("Episode is not published")

            # Generate presigned URL for streaming
            return self._s3_service.generate_download_presigned_url(episode.s3_key)
