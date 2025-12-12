from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from template.persistence.base import Base


class Note(Base):
    __tablename__ = "Note"

    note_id: Mapped[UUID] = mapped_column(sa.UUID(), primary_key=True)
    author_id: Mapped[UUID] = mapped_column(sa.UUID())
    text: Mapped[str] = mapped_column(sa.String(length=250))

    @classmethod
    def new(cls, note_id: UUID, author_id: UUID, text: str) -> "Note":
        if not text:
            raise ValueError("Can't create empty note")
        return Note(note_id=note_id, author_id=author_id, text=text)
    