from http import HTTPStatus
from typing import Annotated, Awaitable, Callable, Protocol, cast

from dishka import FromComponent
from dishka.integrations.fastapi import inject
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from commons.auth import domain
from commons.auth.domain import Role, UserClaims


class TokenService(Protocol):

    def verify(self, token: str) -> UserClaims: ...


class AuthorizationFactory(Protocol):

    def __call__(
        self, allowed_roles: list[Role] | None = None
    ) -> Callable[[], UserClaims]: ...


class AuthConfig(BaseModel):
    token_url: str
    refresh_url: str


def create_authorization_guard(config: AuthConfig) -> AuthorizationFactory:
    bearer = OAuth2PasswordBearer(
        tokenUrl=config.token_url,
        refreshUrl=config.refresh_url,
    )

    def authorize(
        allowed_roles: list[Role] | None = None,
    ) -> Callable[[], Awaitable[UserClaims]]:

        @inject
        async def role_guard(
            token: Annotated[str, Depends(bearer)],
            token_service: Annotated[TokenService, FromComponent()],
        ) -> UserClaims:
            claims = token_service.verify(token)
            if not domain.can_access_with_roles(claims.role, allowed_roles):
                assert allowed_roles is not None
                raise HTTPException(
                    detail=f"User does not have enough permissions: must be one of {[r.value for r in allowed_roles]}",
                    status_code=HTTPStatus.FORBIDDEN,
                )

            return claims

        return cast(Callable[[], Awaitable[UserClaims]], role_guard)

    return authorize  # pyright: ignore[reportReturnType]
