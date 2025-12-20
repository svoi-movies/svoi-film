from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from commons.auth.domain import Role, UserClaims
from commons.auth.guards import create_authorization_guard
from commons.ddd.errors import DomainError
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path

from moderator.api import models
from moderator.config import Config
from moderator.use_cases.auth_service import AuthServiceError
from moderator.use_cases.commands import ModerationCommands
from moderator.use_cases.interfaces import AuthUserData
from moderator.use_cases.queries import ModerationQueries

router = APIRouter(route_class=DishkaRoute)
config = Config()  # pyright: ignore[reportCallIssue]
authorize = create_authorization_guard(config.auth)


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Authorization header is required",
        )
    return authorization


def _map_domain_error(err: DomainError) -> HTTPException:
    status = (
        HTTPStatus.NOT_FOUND
        if "not found" in str(err).lower()
        else HTTPStatus.CONFLICT
    )
    raise HTTPException(status_code=status, detail=str(err)) from err


@router.post(
    "/moderators",
    response_model=models.ModeratorResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_moderator",
)
async def create_moderator(
    req: Annotated[models.CreateModeratorRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[ModerationCommands],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> models.ModeratorResponse:
    bearer_token = _extract_bearer_token(authorization)
    try:
        moderator = await commands.create_moderator(
            user=AuthUserData(**req.user.model_dump()),
            bearer_token=bearer_token,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ModeratorResponse.model_validate(
        moderator, from_attributes=True
    )


@router.delete(
    "/moderators/{moderator_id:uuid}",
    response_model=models.ModeratorResponse,
    status_code=HTTPStatus.OK,
    operation_id="delete_moderator",
)
async def delete_moderator(
    moderator_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[ModerationCommands],
) -> models.ModeratorResponse:
    try:
        moderator = await commands.delete_moderator(moderator_id)
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModeratorResponse.model_validate(
        moderator, from_attributes=True
    )


@router.get(
    "/moderators/{moderator_id:uuid}",
    response_model=models.ModeratorResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_moderator",
)
async def get_moderator(
    moderator_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    queries: FromDishka[ModerationQueries],
) -> models.ModeratorResponse:
    try:
        moderator = await queries.get_moderator(moderator_id)
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModeratorResponse.model_validate(
        moderator, from_attributes=True
    )


@router.post(
    "/moderation-requests",
    response_model=models.ModerationRequestResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="request_moderation",
)
async def request_moderation(
    req: Annotated[models.CreateModerationRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.CONTENT_OWNER]))
    ],
    commands: FromDishka[ModerationCommands],
) -> models.ModerationRequestResponse:
    try:
        moderation_request = await commands.request_moderation(
            episode_id=req.episode_id,
            content_owner_id=req.content_owner_id,
        )
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModerationRequestResponse.model_validate(
        moderation_request, from_attributes=True
    )


@router.post(
    "/moderation-requests/{moderation_request_id:uuid}/approve",
    response_model=models.ModerationRequestResponse,
    status_code=HTTPStatus.OK,
    operation_id="approve_moderation_request",
)
async def approve_moderation(
    moderation_request_id: Annotated[UUID, Path()],
    req: Annotated[models.ResolveModerationRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    commands: FromDishka[ModerationCommands],
) -> models.ModerationRequestResponse:
    try:
        moderation_request = await commands.approve_moderation(
            moderation_request_id=moderation_request_id,
            moderator_id=req.moderator_id,
        )
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModerationRequestResponse.model_validate(
        moderation_request, from_attributes=True
    )


@router.post(
    "/moderation-requests/{moderation_request_id:uuid}/reject",
    response_model=models.ModerationRequestResponse,
    status_code=HTTPStatus.OK,
    operation_id="reject_moderation_request",
)
async def reject_moderation(
    moderation_request_id: Annotated[UUID, Path()],
    req: Annotated[models.ResolveModerationRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    commands: FromDishka[ModerationCommands],
) -> models.ModerationRequestResponse:
    try:
        moderation_request = await commands.reject_moderation(
            moderation_request_id=moderation_request_id,
            moderator_id=req.moderator_id,
        )
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModerationRequestResponse.model_validate(
        moderation_request, from_attributes=True
    )


@router.get(
    "/moderation-requests/{moderation_request_id:uuid}",
    response_model=models.ModerationRequestResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_moderation_request",
)
async def get_moderation_request(
    moderation_request_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims,
        Depends(
            authorize(
                allowed_roles=[
                    Role.ADMIN,
                    Role.MODERATOR,
                    Role.CONTENT_OWNER,
                ]
            )
        ),
    ],
    queries: FromDishka[ModerationQueries],
) -> models.ModerationRequestResponse:
    try:
        moderation_request = await queries.get_moderation_request(
            moderation_request_id
        )
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ModerationRequestResponse.model_validate(
        moderation_request, from_attributes=True
    )


@router.get("/health", status_code=HTTPStatus.OK, include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
