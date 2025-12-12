from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Path
from commons.auth import create_authorization_guard

notes_router = APIRouter(prefix="/notes")

authorize = create_authorization_guard(
    token_url="http://localhost:8080/token_url", 
    verification_key="", 
    algorithms=["HS256"],
)


@notes_router.post("/{id}")
async def create_note(
    id: Annotated[UUID, Path()],
    user: Annotated[UserClaims, create_authorization_guard]
) -> 