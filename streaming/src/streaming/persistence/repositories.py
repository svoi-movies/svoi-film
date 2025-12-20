from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from streaming.domain.viewer import Viewer
from streaming.domain.title import Title
from streaming.domain.episode import Episode
from streaming.domain.viewing_session import ViewingSession
from streaming.persistence.schema import viewers, titles, episodes, viewing_sessions


class ViewerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, viewer: Viewer) -> None:
        self._session.add(viewer)

    async def save(self, viewer: Viewer) -> None:
        await self._session.merge(viewer)

    async def get_by_id(self, viewer_id: UUID) -> Viewer:
        result = await self._session.execute(
            sa.select(Viewer).where(viewers.c.id == viewer_id)
        )
        return result.scalar_one()


class TitleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, title: Title) -> None:
        self._session.add(title)

    async def save(self, title: Title) -> None:
        await self._session.merge(title)

    async def get_by_id(self, title_id: UUID) -> Title:
        result = await self._session.execute(
            sa.select(Title).where(titles.c.id == title_id)
        )
        return result.scalar_one()


class EpisodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, episode: Episode) -> None:
        self._session.add(episode)

    async def save(self, episode: Episode) -> None:
        await self._session.merge(episode)

    async def get_by_id(self, episode_id: UUID) -> Episode:
        result = await self._session.execute(
            sa.select(Episode).where(episodes.c.id == episode_id)
        )
        return result.scalar_one()


class ViewingSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, session: ViewingSession) -> None:
        self._session.add(session)

    async def save(self, session: ViewingSession) -> None:
        await self._session.merge(session)

    async def get_by_id(self, session_id: UUID) -> ViewingSession:
        result = await self._session.execute(
            sa.select(ViewingSession).where(viewing_sessions.c.id == session_id)
        )
        return result.scalar_one()
