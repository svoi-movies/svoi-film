import os
from typing import Generator
from unittest import mock

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer

from moderator.persistence.schema import mapper_registry
from commons.auth.domain import Role, UserClaims
from commons.auth.service import JwtTokenService

db_container = PostgresContainer(image="postgres:17.4")


@pytest.fixture(scope="module", autouse=True)
def setup(request) -> Generator[None]:
    db_container.start()

    def remove_container():
        db_container.stop()

    request.addfinalizer(remove_container)

    db_url = db_container.get_connection_url(driver="asyncpg")
    overrides = {
        "APP_DB__DSN": db_url,
        "APP_DB__EXPIRE_ON_COMMIT": "false",
        "APP_DB_DSN": db_url,
        "APP_DOTENV_FILE_PATH": ".dev/secrets",
        "APP_SECRET_DIR_PATH": "./.dev/secrets",
        "APP_RABBIT__DSN": "amqp://rabbitmq:rabbitmq@localhost:5672/",
        "APP_AUTH__TOKEN_URL": "/auth/login",
        "APP_AUTH__REFRESH_URL": "/auth/refresh",
        "APP_AUTH_CLIENT__BASE_URL": "http://auth:8001",
        "APP_JWT__VERIFYING_KEY": "dummy-key",
    }

    with mock.patch.dict(os.environ, overrides):
        print(os.environ.get("APP_DB__DSN"))
        yield


@pytest.fixture(scope="module")
def migrate(setup) -> Generator[None]:
    from alembic import command
    from alembic.config import Config as AlembicConfig

    alembic_cfg = AlembicConfig("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield


@pytest.fixture(scope="function")
def engine() -> AsyncEngine:
    return create_async_engine(url=db_container.get_connection_url(driver="asyncpg"))


@pytest_asyncio.fixture(scope="function")
async def clean_tables(migrate, engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        for _, table in mapper_registry.metadata.tables.items():
            await conn.execute(sa.delete(table).where(sa.true()))


@pytest.fixture(scope="function")
def app() -> FastAPI:
    from uuid import UUID

    from moderator.api import create_app
    from moderator.api import app as api_app
    from moderator.use_cases.auth_service import HttpxAuthService
    from commons.auth.service import JwtTokenService

    async def fake_create_user(self, user, bearer_token):  # type: ignore[override]
        return UUID("00000000-0000-0000-0000-000000000999")

    # Avoid real HTTP calls to auth during tests.
    HttpxAuthService.create_moderator_user = fake_create_user  # type: ignore[method-assign]

    def fake_verify(self, token: str):  # type: ignore[override]
        role = {
            "admin-token": Role.ADMIN,
            "moderator-token": Role.MODERATOR,
            "content-owner-token": Role.CONTENT_OWNER,
        }.get(token, Role.ADMIN)
        return UserClaims(
            sub=UUID("00000000-0000-0000-0000-000000000123"),
            sid=UUID("00000000-0000-0000-0000-000000000321"),
            email="user@example.com",
            first_name="Test",
            last_name="User",
            role=role,
        )

    JwtTokenService.verify = fake_verify  # type: ignore[method-assign]

    async def noop_declare_exchanges(container):  # type: ignore[override]
        return None

    api_app.declare_exchanges = noop_declare_exchanges  # type: ignore[assignment]

    return create_app()


@pytest.fixture(scope="function")
def test_client(app: FastAPI) -> TestClient:
    return TestClient(app)
