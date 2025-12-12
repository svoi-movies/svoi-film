from typing import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from template.entities.note import Note


class NoteRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def add(self, note: Note) -> None:
        self._session.add(note)
    
    async def get_by_id(self, note_id: UUID) -> Note | None:
        result = await self._session.scalars(sa.select(Note).where(Note.note_id == note_id))
        return result.first()

    async def search(self, query: str) -> Sequence[Note]:
        result = await self._session.scalars(sa.select(Note).where(Note.text.like(f"%{query}%")))
        return result.all()
    
    async def delete(self, note_id: UUID) -> None:
        await self._session.execute(sa.delete(Note).where(Note.note_id == note_id))
