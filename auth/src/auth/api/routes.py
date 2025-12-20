from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from commons.auth.domain import Role as AuthRole
from commons.auth.domain import UserClaims
from commons.auth.guards import create_authorization_guard
from commons.ddd.errors import DomainError
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Path, Response

from auth.api import models
from auth.config import Config
from auth.use_cases.commands import UserCommands
from auth.use_cases.queries import UserQueries

router = APIRouter(route_class=DishkaRoute)

authorize = create_authorization_guard(config=Config().auth)


@router.post(
    "/users/verify-email",
    response_class=Response,
    status_code=HTTPStatus.NO_CONTENT,
)
async def verify_email(
    user_claims: Annotated[UserClaims, Depends(authorize())],
    commands: FromDishka[UserCommands],
    verification_code: Annotated[str, Form()],
) -> None:
    await commands.verify_email(user_claims.user_id, verification_code)


@router.post("/auth/login")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    commands: FromDishka[UserCommands],
) -> models.LoginResponse:
    try:
        token = await commands.login(email=username, password=password)
        return models.LoginResponse.model_validate(token, from_attributes=True)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=str(e))


@router.post(
    "/users/register",
    operation_id="self_register",
)
async def self_register(
    req: Annotated[models.SelfRegisterRequest, Body()],
    commands: FromDishka[UserCommands],
) -> models.SelfRegisterResponse:
    user = await commands.self_register(
        role_name=req.role,
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        password=req.password,
    )

    return models.SelfRegisterResponse(id=user.id)  # type: ignore


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
) -> models.GetMeResponse:
    user = await queries.get_me(user_id)
    return models.GetMeResponse.model_validate(user, from_attributes=True)


@router.post(
    "/roles",
    operation_id="create_role",
    status_code=HTTPStatus.CREATED,
)
async def create_role(
    req: Annotated[models.CreateRoleRequest, Body()],
    commands: FromDishka[UserCommands],
    user_claims: Annotated[UserClaims, Depends(authorize([AuthRole.ADMIN]))],
) -> models.CreateRoleResponse:
    role = await commands.create_role(
        name=req.name,
        allow_self_registration=req.allow_self_registration,
        creator_role_id=req.creator_role_id,
    )

    return models.CreateRoleResponse(id=role.id)  # type: ignore


@router.get(
    "/roles",
    operation_id="list_roles",
)
async def list_roles(
    queries: FromDishka[UserQueries],
    user_claims: Annotated[UserClaims, Depends(authorize())],
) -> list[models.RoleResponse]:
    roles = await queries.list_roles()
    return [
        models.RoleResponse.model_validate(role, from_attributes=True) for role in roles
    ]


@router.post(
    "/users",
    operation_id="create_user",
    status_code=HTTPStatus.CREATED,
)
async def create_user(
    req: Annotated[models.CreateUserRequest, Body()],
    commands: FromDishka[UserCommands],
    user_claims: Annotated[UserClaims, Depends(authorize())],
) -> models.CreateUserResponse:
    user = await commands.create_user(
        creator_user_id=user_claims.user_id,
        target_role_name=req.role,
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        password=req.password,
    )

    return models.CreateUserResponse(id=user.id)  # type: ignore
