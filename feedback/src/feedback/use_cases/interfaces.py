from abc import ABC, abstractmethod

from commons.unit_of_work.abc import UnitOfWork

from feedback.persistence.repositories import (
    FeedbackEstimationRepository,
    FeedbackRepository,
    TitleRepository,
    TitleScoreRepository,
)


class FeedbackUnitOfWork(UnitOfWork, ABC):
    @property
    @abstractmethod
    def titles(self) -> TitleRepository: ...

    @property
    @abstractmethod
    def title_scores(self) -> TitleScoreRepository: ...

    @property
    @abstractmethod
    def feedbacks(self) -> FeedbackRepository: ...

    @property
    @abstractmethod
    def feedback_estimations(self) -> FeedbackEstimationRepository: ...
