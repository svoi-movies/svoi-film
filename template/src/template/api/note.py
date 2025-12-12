from typing import Annotated
from uuid import UUID

from commons.auth import Permission, UserClaims, create_authorization_guard
from fastapi import APIRouter, Depends, Path

notes_router = APIRouter(prefix="/notes")

authorize = create_authorization_guard(
    token_url="http://localhost:8080/token_url",
    verification_key="",
    algorithms=["HS256"],
)


@notes_router.post("/{id}")
async def create_note(
    id: Annotated[UUID, Path()],
    user: Annotated[UserClaims, Depends(authorize({Permission.CREATE_NOTE}))],
) -> None: ...
