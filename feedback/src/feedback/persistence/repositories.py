from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from feedback.domain.models import Feedback, FeedbackEstimation, Title, TitleScore


class TitleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, title_id: UUID) -> Title:
        stmt = sa.select(Title).where(Title.id == title_id)
        result = await self._session.execute(stmt)
        title = result.scalar_one_or_none()
        if title is None:
            raise ValueError(f"Title with id {title_id} not found")
        return title

    async def find_by_id(self, title_id: UUID) -> Title | None:
        stmt = sa.select(Title).where(Title.id == title_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, title: Title) -> None:
        self._session.add(title)

    async def delete(self, title: Title) -> None:
        await self._session.delete(title)


class TitleScoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, score_id: UUID) -> TitleScore:
        result = await self._session.get(TitleScore, score_id)
        if result is None:
            raise ValueError(f"TitleScore with id {score_id} not found")
        return result

    async def find_by_user_and_title(
        self, user_id: UUID, title_id: UUID
    ) -> TitleScore | None:
        stmt = sa.select(TitleScore).where(
            sa.and_(
                TitleScore.user_id == user_id,
                TitleScore.title_id == title_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_avg_by_title(self, title_id: UUID) -> float | None:
        stmt = sa.select(sa.func.avg(TitleScore.score)).where(
            TitleScore.title_id == title_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, score: TitleScore) -> None:
        self._session.add(score)

    async def save(self, score: TitleScore) -> None:
        await self._session.merge(score)


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, feedback_id: UUID) -> Feedback:
        result = await self._session.get(Feedback, feedback_id)
        if result is None:
            raise ValueError(f"Feedback with id {feedback_id} not found")
        return result

    async def find_by_user_and_title(
        self, user_id: UUID, title_id: UUID
    ) -> Feedback | None:
        stmt = sa.select(Feedback).where(
            sa.and_(
                Feedback.user_id == user_id,
                Feedback.title_id == title_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_by_title(self, title_id: UUID) -> list[Feedback]:
        stmt = sa.select(Feedback).where(Feedback.title_id == title_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    def add(self, feedback: Feedback) -> None:
        self._session.add(feedback)

    async def save(self, feedback: Feedback) -> None:
        await self._session.merge(feedback)


class FeedbackEstimationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, estimation_id: UUID) -> FeedbackEstimation:
        result = await self._session.get(FeedbackEstimation, estimation_id)
        if result is None:
            raise ValueError(f"FeedbackEstimation with id {estimation_id} not found")
        return result

    async def find_by_user_and_feedback(
        self, user_id: UUID, feedback_id: UUID
    ) -> FeedbackEstimation | None:
        stmt = sa.select(FeedbackEstimation).where(
            sa.and_(
                FeedbackEstimation.user_id == user_id,
                FeedbackEstimation.feedback_id == feedback_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, estimation: FeedbackEstimation) -> None:
        self._session.add(estimation)

    async def save(self, estimation: FeedbackEstimation) -> None:
        await self._session.merge(estimation)
