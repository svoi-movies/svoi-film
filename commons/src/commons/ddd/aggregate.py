from datetime import datetime
from typing import Any, Protocol, Sequence


class DomainEvent(Protocol):
    type: str
    category: str
    occurred_on: datetime


class Id(Protocol):
    def __eq__(self, other: Any) -> bool: ...


class Entity[TId: Id]:
    """
    Entity это базовый тип для всех сущностей, у которых есть Id.
    Реализует сравнение по Id и типу.
    Удаляет __hash__, поэтому ее нельзя положить в словарь в качестве ключа.
    """

    __hash__ = None  # pyright: ignore[reportAssignmentType]

    def __init__(self, entity_id: TId) -> None:
        self._id = entity_id

    @property
    def id(self) -> TId:
        return self._id

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, type(self)):
            return NotImplemented

        return self.id == value.id


class Aggregate[TId: Id, TEvent: DomainEvent](Entity[TId]):
    """
    Aggregate – это базовый тип для всех агрегатов. Наследует Entity.
    Дополнительно может генерировать события предметной области через _push_event.
    """

    def __init__(self, aggregate_id: TId) -> None:
        super().__init__(aggregate_id)
        self.__events: list[TEvent] = []

    def _push_event(self, event: TEvent) -> None:
        self.__events.append(event)

    def collect_events(self) -> Sequence[DomainEvent]:
        return self.__events[:]
