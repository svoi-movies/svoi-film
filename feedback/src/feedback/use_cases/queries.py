from uuid import UUID

from feedback.domain.models import Feedback, TitleScore
from feedback.use_cases.interfaces import FeedbackUnitOfWork


class FeedbackQueries:
    def __init__(self, uow: FeedbackUnitOfWork) -> None:
        self._uow = uow

    async def get_avg_title_score(self, title_id: UUID) -> float:
        async with self._uow:
            avg = await self._uow.title_scores.get_avg_by_title(title_id)
            return avg if avg is not None else 0.0

    async def get_user_title_score(
        self, user_id: UUID, title_id: UUID
    ) -> TitleScore | None:
        async with self._uow:
            return await self._uow.title_scores.find_by_user_and_title(user_id, title_id)

    async def get_all_feedbacks(self, title_id: UUID) -> list[Feedback]:
        async with self._uow:
            return await self._uow.feedbacks.find_all_by_title(title_id)
