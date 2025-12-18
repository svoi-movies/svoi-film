from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from feedback.domain.models import Feedback, FeedbackEstimation, Title, TitleScore
from feedback.use_cases.interfaces import FeedbackUnitOfWork


class FeedbackCommands:
    def __init__(
        self,
        uow: FeedbackUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider

    async def set_title_score(
        self, user_id: UUID, title_id: UUID, score: int
    ) -> TitleScore:
        async with self._uow:
            existing_score = await self._uow.title_scores.find_by_user_and_title(
                user_id, title_id
            )

            if existing_score:
                existing_score.update_score(score, self._datetime_provider.now_utc)
                await self._uow.title_scores.save(existing_score)
                await self._uow.commit()
                return existing_score
            else:
                new_score = TitleScore.new(
                    score_id=self._uuid_provider.new_v4(),
                    user_id=user_id,
                    title_id=title_id,
                    score=score,
                    now=self._datetime_provider.now_utc,
                )
                self._uow.title_scores.add(new_score)
                await self._uow.commit()
                return new_score

    async def add_feedback(
        self, user_id: UUID, title_id: UUID, text: str
    ) -> Feedback:
        async with self._uow:
            new_feedback = Feedback.new(
                feedback_id=self._uuid_provider.new_v4(),
                user_id=user_id,
                title_id=title_id,
                text=text,
                now=self._datetime_provider.now_utc,
            )
            self._uow.feedbacks.add(new_feedback)
            await self._uow.commit()
            return new_feedback

    async def update_feedback(
        self, user_id: UUID, title_id: UUID, text: str
    ) -> Feedback:
        async with self._uow:
            feedback = await self._uow.feedbacks.find_by_user_and_title(
                user_id, title_id
            )
            if not feedback:
                raise ValueError("Feedback not found")

            if feedback.user_id != user_id:
                raise ValueError("You can only update your own feedback")

            feedback.update_text(text, self._datetime_provider.now_utc)
            await self._uow.feedbacks.save(feedback)
            await self._uow.commit()
            return feedback

    async def set_feedback_estimation(
        self, user_id: UUID, feedback_id: UUID, is_positive: bool
    ) -> FeedbackEstimation:
        async with self._uow:
            existing = await self._uow.feedback_estimations.find_by_user_and_feedback(
                user_id, feedback_id
            )

            if existing:
                existing.update(is_positive, self._datetime_provider.now_utc)
                await self._uow.feedback_estimations.save(existing)
                await self._uow.commit()
                return existing
            else:
                new_estimation = FeedbackEstimation.new(
                    estimation_id=self._uuid_provider.new_v4(),
                    user_id=user_id,
                    feedback_id=feedback_id,
                    is_positive=is_positive,
                    now=self._datetime_provider.now_utc,
                )
                self._uow.feedback_estimations.add(new_estimation)
                await self._uow.commit()
                return new_estimation

    async def add_title(self, title_id: UUID) -> Title:
        async with self._uow:
            existing = await self._uow.titles.find_by_id(title_id)
            if existing:
                return existing

            new_title = Title.new(
                title_id=title_id,
                now=self._datetime_provider.now_utc,
            )
            self._uow.titles.add(new_title)
            await self._uow.commit()
            return new_title

    async def delete_title(self, title_id: UUID) -> None:
        async with self._uow:
            title = await self._uow.titles.find_by_id(title_id)
            if title:
                await self._uow.titles.delete(title)
                await self._uow.commit()
