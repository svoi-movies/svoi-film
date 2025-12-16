import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from pytz import UTC


class DateTimeProvider(ABC):

    @property
    @abstractmethod
    def now_utc(self) -> datetime: ...


class DefaultDateTimeProvider(DateTimeProvider):
    @property
    def now_utc(self) -> datetime:
        return datetime.now(UTC)


class UUIDProvider(ABC):

    @abstractmethod
    def new_v4(self) -> UUID: ...


class DefaultUUIDProvider(UUIDProvider):
    def new_v4(self) -> UUID:
        return uuid.uuid4()
