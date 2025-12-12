from enum import Enum
from http import HTTPStatus
from typing import Annotated, Callable, Protocol, cast
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWSError, jws
from pydantic import BaseModel


class Role(Enum):
    MODERATOR = "moderator"
    VIEWER = "viewer"
    CONTENT_OWNER = "content_owner"
    ADMIN = "admin"


class UserClaims(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    role: Role


class AuthorizationFactory(Protocol):

    def __call__(
        self, allowed_roles: list[Role] | None = None
    ) -> Callable[[], UserClaims]: ...


def create_authorization_guard(
    token_url: str,
    verification_key: str,
    algorithms: list[str],
) -> AuthorizationFactory:
    bearer = OAuth2PasswordBearer(tokenUrl=token_url)

    def get_current_user(
        bearer_token: Annotated[str, Depends(bearer)],
    ) -> UserClaims:
        try:
            payload = jws.verify(
                token=bearer_token,
                key=verification_key,
                algorithms=algorithms,
                verify=True,
            )

            return UserClaims.model_validate_json(payload)
        except JWSError as e:
            raise HTTPException(
                detail=f"Invalid access token: {e}",
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except ExpiredSignatureError:
            raise HTTPException(
                detail="Access token has expired",
                status_code=HTTPStatus.UNAUTHORIZED,
            )

    def authorize(allowed_roles: list[Role]) -> Callable[[], UserClaims]:
        def permissions_guard(
            current_user: Annotated[UserClaims, Depends(get_current_user)],
        ) -> UserClaims:
            print(allowed_roles, current_user)
            if allowed_roles and current_user.role not in allowed_roles:
                raise HTTPException(
                    detail=f"User does not have enough permissions: must be one of {[r.value for r in allowed_roles]}",
                    status_code=HTTPStatus.FORBIDDEN,
                )

            return current_user

        return cast(Callable[[], UserClaims], permissions_guard)

    return authorize
