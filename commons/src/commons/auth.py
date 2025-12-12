from enum import Enum
from http import HTTPStatus
from typing import Annotated, Callable, cast
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWSError, jws
from pydantic import BaseModel


class Permission(Enum): ...


class UserClaims(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    permissions: set[Permission]


def create_authorization_guard(
    token_url: str,
    verification_key: str,
    algorithms: list[str],
) -> Callable[[set[Permission]], Callable[[], UserClaims]]:
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
        except JWSError:
            raise HTTPException(
                detail="Invalid access token",
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except ExpiredSignatureError:
            raise HTTPException(
                detail="Access token has expired",
                status_code=HTTPStatus.UNAUTHORIZED,
            )

    def authorize(permissions: set[Permission]) -> Callable[[], UserClaims]:
        def permissions_guard(
            current_user: Annotated[UserClaims, Depends(get_current_user)],
        ) -> UserClaims:
            if permissions - current_user.permissions:
                raise HTTPException(
                    detail="User does not have enough permissions",
                    status_code=HTTPStatus.FORBIDDEN,
                )

            return current_user

        return cast(Callable[[], UserClaims], permissions_guard)

    return authorize
