from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.asyncio
async def test__create_role__can_login_as_root(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    response = test_client.post(
        "/auth/login",
        data={"username": "root@svoifilm.com", "password": "rootroot!23"},
    )
    assert response.status_code == HTTPStatus.OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test__create_role__login_returns_401_when_password_incorrect(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    response = test_client.post(
        "/auth/login",
        data={"username": "root@svoifilm.com", "password": "incorrect password"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
