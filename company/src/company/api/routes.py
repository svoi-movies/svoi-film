from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from commons.auth.domain import Role, UserClaims
from commons.auth.guards import create_authorization_guard
from commons.ddd.errors import DomainError
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path

from company.api import models
from company.use_cases.auth_service import AuthServiceError
from company.use_cases.commands import CompanyCommands
from company.use_cases.interfaces import AuthUserData
from company.use_cases.queries import CompanyQueries
from company.config import Config

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
    "/companies",
    response_model=models.CompanyResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_company",
)
async def create_company(
    req: Annotated[models.CreateCompanyRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[CompanyCommands],
) -> models.CompanyResponse:
    try:
        company = await commands.create_company(name=req.name)
    except DomainError as e:
        raise _map_domain_error(e)
    return models.CompanyResponse.model_validate(company, from_attributes=True)


@router.post(
    "/content-owners",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_content_owner",
)
async def create_content_owner(
    req: Annotated[models.CreateContentOwnerRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    commands: FromDishka[CompanyCommands],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> models.ContentOwnerResponse:
    bearer_token = _extract_bearer_token(authorization)
    try:
        content_owner = await commands.add_content_owner(
            company_id=req.company_id,
            user=AuthUserData(**req.user.model_dump()),
            permissions=req.permissions,
            bearer_token=bearer_token,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.patch(
    "/companies/{company_id:uuid}/content-owners/{content_owner_id:uuid}/permissions",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="update_company_content_owner_permissions",
)
async def update_content_owner_permissions(
    company_id: Annotated[UUID, Path()],
    content_owner_id: Annotated[UUID, Path()],
    req: Annotated[models.UpdateContentOwnerPermissionsRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[CompanyCommands],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await commands.update_content_owner_permissions(
            company_id=company_id,
            content_owner_id=content_owner_id,
            permissions=req.permissions,
        )
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.patch(
    "/content-owners/{content_owner_id:uuid}/permissions",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="update_content_owner_permissions",
)
async def update_content_owner_permissions_by_id(
    content_owner_id: Annotated[UUID, Path()],
    req: Annotated[models.UpdatePermissionsRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    commands: FromDishka[CompanyCommands],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await commands.update_content_owner_permissions_by_id(
            content_owner_id=content_owner_id,
            permissions=req.permissions,
        )
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.delete(
    "/companies/{company_id:uuid}/content-owners/{content_owner_id:uuid}",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="remove_company_content_owner",
)
async def remove_content_owner(
    company_id: Annotated[UUID, Path()],
    content_owner_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[CompanyCommands],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await commands.remove_content_owner(
            company_id=company_id,
            content_owner_id=content_owner_id,
        )
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.delete(
    "/content-owners/{content_owner_id:uuid}",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="delete_content_owner",
)
async def delete_content_owner_by_id(
    content_owner_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    commands: FromDishka[CompanyCommands],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await commands.remove_content_owner_by_id(
            content_owner_id
        )
    except DomainError as e:
        raise _map_domain_error(e)

    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.get(
    "/companies/{company_id:uuid}",
    response_model=models.CompanyResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_company",
)
async def get_company(
    company_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    queries: FromDishka[CompanyQueries],
) -> models.CompanyResponse:
    try:
        company = await queries.get_company(company_id)
    except DomainError as e:
        raise _map_domain_error(e)
    return models.CompanyResponse.model_validate(company, from_attributes=True)


@router.get(
    "/companies/{company_id:uuid}/content-owners/{content_owner_id:uuid}",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_company_content_owner",
)
async def get_content_owner(
    company_id: Annotated[UUID, Path()],
    content_owner_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    queries: FromDishka[CompanyQueries],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await queries.get_content_owner(
            company_id=company_id,
            content_owner_id=content_owner_id,
        )
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.get(
    "/content-owners/{content_owner_id:uuid}",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_content_owner",
)
async def get_content_owner_by_id(
    content_owner_id: Annotated[UUID, Path()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.MODERATOR]))
    ],
    queries: FromDishka[CompanyQueries],
) -> models.ContentOwnerResponse:
    try:
        content_owner = await queries.get_content_owner_by_id(content_owner_id)
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.post(
    "/companies/{company_id:uuid}/content-owners",
    response_model=models.ContentOwnerResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="add_company_content_owner",
)
async def add_content_owner(
    company_id: Annotated[UUID, Path()],
    req: Annotated[models.AddContentOwnerRequest, Body()],
    _: Annotated[
        UserClaims, Depends(authorize(allowed_roles=[Role.ADMIN]))
    ],
    commands: FromDishka[CompanyCommands],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> models.ContentOwnerResponse:
    bearer_token = _extract_bearer_token(authorization)
    try:
        content_owner = await commands.add_content_owner(
            company_id=company_id,
            user=AuthUserData(**req.user.model_dump()),
            permissions=req.permissions,
            bearer_token=bearer_token,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except DomainError as e:
        raise _map_domain_error(e)
    return models.ContentOwnerResponse.model_validate(
        content_owner, from_attributes=True
    )


@router.get("/health", status_code=HTTPStatus.OK, include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
