from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from commons.auth.domain import UserClaims
from commons.auth.guards import create_authorization_guard
from commons.utils.common_providers import UUIDProvider
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Form, Path, Response

from auth.api import models
from auth.config import Config
from auth.use_cases.commands import UserCommands
from auth.use_cases.interfaces import UserUnitOfWork
from auth.use_cases.queries import UserQueries

router = APIRouter(route_class=DishkaRoute)

authorize = create_authorization_guard(config=Config().auth)


@router.post(
    "/users/activate",
    response_class=Response,
    status_code=HTTPStatus.NO_CONTENT,
)
async def activate_user(
    # user_claims: Annotated[UserClaims, Depends(authorize(allowed_roles=[Role.VIEWER]))],
    uuid_provider: FromDishka[UUIDProvider],
    uow: FromDishka[UserUnitOfWork],
    activation_code: Annotated[str, Form()],
) -> None:
    raise NotImplementedError


@router.post("/auth/login")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    commands: FromDishka[UserCommands],
) -> models.LoginResponse:
    return models.LoginResponse.model_validate(
        await commands.login(email=username, password=password),
        from_attributes=True,
    )


@router.post(
    "/users/viewer",
    operation_id="create_viewer",
)
async def create_viewer(
    req: Annotated[models.CreateViewerRequest, Body()],
    commands: FromDishka[UserCommands],
) -> models.CreateViewerResponse:
    user = await commands.create_viewer(
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        password=req.password,
    )

    return models.CreateViewerResponse(id=user.id)  # type: ignore


@router.get(
    "/users/me",
    operation_id="get_me",
)
async def get_me(
    queries: FromDishka[UserQueries],
    user_claims: Annotated[UserClaims, Depends(authorize())],
) -> models.GetMeResponse:
    user = await queries.get_me(user_claims.user_id)
    return models.GetMeResponse.model_validate(user, from_attributes=True)


@router.get(
    "/users/{user_id:uuid}",
    operation_id="get_user_by_id",
)
async def get_user_by_id(
    user_id: Annotated[UUID, Path()],
    queries: FromDishka[UserQueries],
    user_claims: Annotated[UserClaims, Depends(authorize())],
) -> models.CreateViewerResponse:
    raise NotImplementedError
