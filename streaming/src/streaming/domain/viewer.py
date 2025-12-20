from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from commons.ddd.errors import DomainError
from sqlalchemy.orm import reconstructor


@dataclass(frozen=True, slots=True, eq=True)
class ViewerCreatedEvent:
    viewer_id: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True, eq=True)
class ViewerDeletedEvent:
    viewer_id: UUID
    deleted_at: datetime


class Viewer(Aggregate[UUID, Any]):
    def __init__(
        self,
        viewer_id: UUID,
        created_at: datetime,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(viewer_id)
        self._created_at = created_at
        self._deleted_at = deleted_at

    @reconstructor
    def _init_on_load(self) -> None:
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(
        cls,
        viewer_id: UUID,
        now: datetime,
    ) -> "Viewer":
        viewer = cls(
            viewer_id=viewer_id,
            created_at=now,
            deleted_at=None,
        )
        viewer._push_event(
            ViewerCreatedEvent(
                viewer_id=viewer.id,
                created_at=viewer.created_at,
            )
        )
        return viewer

    def delete(self, now: datetime) -> None:
        if self._deleted_at is not None:
            raise DomainError("Viewer is already deleted")

        self._deleted_at = now
        self._push_event(ViewerDeletedEvent(viewer_id=self.id, deleted_at=now))

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None
