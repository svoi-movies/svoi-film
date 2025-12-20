from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from commons.ddd import Aggregate, Validator
from sqlalchemy.orm import reconstructor


class CompanyStatus(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True, eq=True)
class CompanyCreatedEvent:
    company_id: UUID
    name: str
    created_at: datetime


class Company(Aggregate[UUID, Any]):
    def __init__(
        self,
        company_id: UUID,
        name: str,
        status: CompanyStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(company_id)
        self._name = name
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at

        with Validator() as v:
            v.must(lambda: bool(self._name.strip()), "name cannot be empty")
            v.must(
                lambda: self._created_at <= self._updated_at,
                "updated_at cannot precede created_at",
            )

    @reconstructor
    def _init_on_load(self) -> None:
        # SQLAlchemy bypasses __init__ on load; reset domain events storage.
        self._Aggregate__events = []  # type: ignore[attr-defined]

    @classmethod
    def new(cls, company_id: UUID, name: str, now: datetime) -> "Company":
        company = cls(
            company_id=company_id,
            name=name,
            status=CompanyStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        company._push_event(
            CompanyCreatedEvent(
                company_id=company.id,
                name=company.name,
                created_at=company.created_at,
            )
        )
        return company

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> CompanyStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
