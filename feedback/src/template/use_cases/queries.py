from typing import Sequence
from uuid import UUID

from template.entities.note import Note
from template.persistence.note_repository import NoteRepository


async def get_note_by_id(
    note_repository: NoteRepository,
    note_id: UUID,
) -> Note:
    note = await note_repository.get_by_id(note_id)
    if note is None:
        raise ValueError(f"Note with id {note_id} is not found")

    return note

async def search_notes(
    note_repository: NoteRepository,
    query: str,
) -> Sequence[Note]:
    notes = await note_repository.search(query)
    return notes

