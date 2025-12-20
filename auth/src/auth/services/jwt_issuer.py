from datetime import timedelta
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider
from jose import jws

from auth.domain.value_objects import Email
from auth.use_cases.interfaces import (
    JwtIssuer,
    Token,
)


class JoseJwtIssuer(JwtIssuer):
    def __init__(
        self,
        signing_key: str,
        access_token_ttl: timedelta,
        refresh_token_ttl: timedelta,
        date_time_provider: DateTimeProvider,
    ) -> None:
        self._signing_key = signing_key
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._date_time_provider = date_time_provider

    def issue_token(
        self,
        user_id: UUID,
        first_name: str,
        last_name: str,
        email: Email,
        session_id: UUID,
        role: str,
    ) -> Token:
        now = self._date_time_provider.now_utc
        access_claims = {
            "sub": str(user_id),
            "sid": str(session_id),
            "exp": int((now + self._access_token_ttl).timestamp()),
            "first_name": first_name,
            "last_name": last_name,
            "email": email.value,
            "role": role,
            "nbf": int(now.timestamp()),
        }

        refresh_claims = {
            "sub": str(user_id),
            "sid": str(session_id),
            "exp": int((now + self._refresh_token_ttl).timestamp()),
            "nbf": int(now.timestamp()),
        }

        access_token = jws.sign(access_claims, self._signing_key, algorithm="ES256")
        refresh_token = jws.sign(refresh_claims, self._signing_key, algorithm="ES256")
        return Token(
            token_type="Bearer", access_token=access_token, refresh_token=refresh_token
        )
