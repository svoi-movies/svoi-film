import uuid
from http import HTTPStatus
from typing import Annotated

from commons.auth.domain import Role, UserClaims
from commons.auth.guards import create_authorization_guard
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Form, Path, Response
from pydantic import BaseModel

from feedback.config import Config
from feedback.use_cases.commands import FeedbackCommands
from feedback.use_cases.queries import FeedbackQueries

config = Config()  # pyright: ignore[reportCallIssue]

router = APIRouter(route_class=DishkaRoute)

authorize = create_authorization_guard(config=config.auth)


class FeedbackResponse(BaseModel):
    feedback_id: uuid.UUID
    user_id: uuid.UUID
    title_id: uuid.UUID
    text: str


class ScoreResponse(BaseModel):
    score: int


@router.get("/title/{title_id:uuid}/avg_estimation")
async def get_avg_estimation(
    title_id: Annotated[uuid.UUID, Path()],
    queries: FromDishka[FeedbackQueries],
) -> float:
    return await queries.get_avg_title_score(title_id)


@router.get("/title/{title_id:uuid}/estimation")
async def get_user_estimation(
    user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    title_id: Annotated[uuid.UUID, Path()],
    queries: FromDishka[FeedbackQueries],
) -> ScoreResponse | None:
    score = await queries.get_user_title_score(user_claims.user_id, title_id)
    if score is None:
        return None
    return ScoreResponse(score=score.score)


@router.post(
    "/title/{title_id:uuid}/estimation",
    response_class=Response,
    status_code=HTTPStatus.NO_CONTENT,
)
async def set_estimation(
    user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    title_id: Annotated[uuid.UUID, Path()],
    score: Annotated[int, Form()],
    commands: FromDishka[FeedbackCommands],
) -> None:
    await commands.set_title_score(user_claims.user_id, title_id, score)


@router.post("/title/{title_id:uuid}/feedback")
async def add_feedback(
    user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    title_id: Annotated[uuid.UUID, Path()],
    text: Annotated[str, Form()],
    commands: FromDishka[FeedbackCommands],
) -> FeedbackResponse:
    feedback = await commands.add_feedback(user_claims.user_id, title_id, text)
    return FeedbackResponse(
        feedback_id=feedback.id,  # type: ignore
        user_id=feedback.user_id,
        title_id=feedback.title_id,
        text=feedback.text,
    )


@router.post("/title/{title_id:uuid}/feedback/{feedback_id:uuid}/estimation")
async def set_estimation_to_feedback(
    user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    title_id: Annotated[uuid.UUID, Path()],
    feedback_id: Annotated[uuid.UUID, Path()],
    is_positive: Annotated[bool, Form()],
    commands: FromDishka[FeedbackCommands],
) -> None:
    await commands.set_feedback_estimation(
        user_claims.user_id, feedback_id, is_positive
    )


@router.patch("/title/{title_id:uuid}/feedback")
async def patch_feedback(
    user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    new_text: Annotated[str, Body()],
    title_id: Annotated[uuid.UUID, Path()],
    commands: FromDishka[FeedbackCommands],
) -> None:
    await commands.update_feedback(user_claims.user_id, title_id, new_text)


@router.get(
    "/title/{title_id:uuid}/all_feedback",
)
async def get_all_feedback(
    title_id: Annotated[uuid.UUID, Path()],
    queries: FromDishka[FeedbackQueries],
) -> list[FeedbackResponse]:
    feedbacks = await queries.get_all_feedbacks(title_id)
    return [
        FeedbackResponse(
            feedback_id=f.id,  # type: ignore
            user_id=f.user_id,
            title_id=f.title_id,
            text=f.text,
        )
        for f in feedbacks
    ]
