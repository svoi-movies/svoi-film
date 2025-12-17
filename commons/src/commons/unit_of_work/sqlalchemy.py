from abc import ABC
from typing import Any, Protocol, cast, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from .abc import UnitOfWork as AbstractUnitOfWork


@runtime_checkable
class DomainEventsHolder[TEvent: Any](Protocol):

    def collect_events(self) -> list[TEvent]: ...


class UnitOfWork[TEvent: Any](AbstractUnitOfWork, ABC):

    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def __aenter__(self) -> None:
        await self.__session.begin().__aenter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.__session.__aexit__(exc_type, exc, tb)

    async def commit(self) -> None:
        events = self.__collect_events()
        await self.handle_domain_events(events)
        await self.__session.commit()

    async def rollback(self) -> None:
        await self.__session.rollback()

    def __collect_events(self) -> list[TEvent]:
        events: list[TEvent] = []
        objects = [*self.__session.new, *self.__session.identity_map.values()]
        for tracked_object in objects:
            if isinstance(tracked_object, DomainEventsHolder):
                tracked_object = cast(DomainEventsHolder[TEvent], tracked_object)
                events.extend(tracked_object.collect_events())

        return events
