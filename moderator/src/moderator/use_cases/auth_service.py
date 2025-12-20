from uuid import UUID

import httpx
from commons.auth.domain import Role

from moderator.config import AuthClientConfig
from moderator.use_cases.interfaces import AuthService, AuthUserData


class AuthServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class HttpxAuthService(AuthService):
    def __init__(self, config: AuthClientConfig) -> None:
        self._base_url = str(config.base_url).rstrip("/")
        self._timeout = 10.0

    async def create_moderator_user(
        self, user: AuthUserData, bearer_token: str
    ) -> UUID:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            ) as client:
                response = await client.post(
                    "/users",
                    headers={"Authorization": bearer_token},
                    json={
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "password": user.password,
                        "role": Role.MODERATOR.value,
                    },
                )
        except httpx.HTTPError as exc:
            raise AuthServiceError(
                status_code=503, detail=f"Auth service unavailable: {exc}"
            ) from exc

        if response.status_code >= 400:
            detail = self._extract_detail(response)
            raise AuthServiceError(response.status_code, detail)

        payload = response.json()
        try:
            return UUID(str(payload["id"]))
        except Exception as exc:  # noqa: BLE001
            raise AuthServiceError(
                response.status_code,
                "Auth service response missing id",
            ) from exc

    @staticmethod
    def _extract_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
            if isinstance(payload, dict) and "detail" in payload:
                return str(payload["detail"])
            return str(payload)
        except Exception:  # noqa: BLE001
            return response.text or "Auth service error"
