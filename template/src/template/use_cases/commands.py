import uuid
from uuid import UUID

from template.entities.note import Note
from template.persistence.note_repository import NoteRepository


async def create_note(
    note_repository: NoteRepository,
    author_id: UUID,
    text: str,
) -> Note:
    note = Note.new(
        note_id=uuid.uuid4(),
        author_id=author_id,
        text=text,
    )
    await note_repository.add(note)
    
    return note

