import uuid
from http import HTTPStatus
from typing import Annotated
from pydantic import BaseModel
from fastapi import FastAPI, Depends, Path, Response, Body
from commons.auth import Role, UserClaims, create_authorization_guard

app = FastAPI()

authorize = create_authorization_guard(
    token_url="http://127.0.0.1:8000/auth/login",
    algorithms=["ES256"],
    verification_key="""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEBj5YjXsaCvrvnEDcZVCz/whCWbET
Bi5t8va9efjfl1d/adk8iX2eBQ5PbnIxCQnEKbTn52+/Oiz4aLutJUy55Q==
-----END PUBLIC KEY-----""",
)


class Feedback(BaseModel):
    feedback_id: uuid.UUID
    user_id: uuid.UUID
    title_id: uuid.UUID
    feedback: str


@app.get("/title/{title_id:uuid}/avg_estimation")
async def get_avg_estimation(
        title_id: Annotated[uuid.UUID, Path()]
) -> float:
    return 1.0


@app.get("/title/{title_id:uuid}/estimation")
async def get_user_estimation(
        user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
        title_id: Annotated[uuid.UUID, Path()]
) -> None:
    return None


@app.post("/title/{title_id:uuid}/estimation",
          response_class=Response,
          status_code=HTTPStatus.NO_CONTENT,
          )
async def set_estimation(
        user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
        title_id: Annotated[uuid.UUID, Path()]
) -> None:
    return None


@app.post("/title/{title_id:uuid}/feedback")
async def add_feedback(
        user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
        title_id: Annotated[uuid.UUID, Path()]
) -> None:
    return None


@app.post("/title/{title_id:uuid}/feedback/{feedback_id:uuid}/estimation")
async def set_set_estimation_to_feedback(
        user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
        title_id: Annotated[uuid.UUID, Path()],
        feedback_id: Annotated[uuid.UUID, Path()]
) -> None:
    return None


@app.puch("/title/{title_id:uuid}/feedback")
async def puch_feedback(
        new_text: Annotated[uuid.UUID, Body()],
        title_id: Annotated[uuid.UUID, Path()]
) -> None:
    return None


@app.get("/title/{title_id:uuid}/all_feedback",
         response_class=Response,
         status_code=HTTPStatus.NO_CONTENT,
         )
async def get_all_feedback(
        title_id: Annotated[uuid.UUID, Path()]
) -> list[Feedback]:
    return []
