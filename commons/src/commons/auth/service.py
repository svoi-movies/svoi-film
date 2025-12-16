from http import HTTPStatus

from commons.auth.domain import UserClaims
from fastapi import HTTPException
from jose import ExpiredSignatureError, JWSError, jws


class JwtTokenService:

    def __init__(self, verification_key: str, algorithm: str) -> None:
        self.__verification_key = verification_key
        self.__algorithm = algorithm

    def verify(self, token: str) -> UserClaims:
        try:
            print(token)
            payload = jws.verify(
                token=token,
                key=self.__verification_key,
                algorithms=[self.__algorithm],
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
