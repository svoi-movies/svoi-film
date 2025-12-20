import os
from typing import Generator
from unittest import mock

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.core.wait_strategies import HealthcheckWaitStrategy
from testcontainers.postgres import PostgresContainer

from auth.domain.value_objects import Email
from auth.persistence.schema import mapper_registry, roles, sessions, users

db_container = PostgresContainer(image="postgres:17.4")


@pytest.fixture(scope="module", autouse=True)
def setup(request) -> Generator[None]:
    db_container.start()

    db_container.waiting_for(HealthcheckWaitStrategy())

    def remove_container():
        db_container.stop()

    request.addfinalizer(remove_container)

    db_url = db_container.get_connection_url(driver="asyncpg")
    overrides = {
        "APP_DB__DSN": db_url,
        "APP_DB_DSN": db_url,
        "APP_DOTENV_FILE_PATH": ".dev/secrets",
        "APP_SECRET_DIR_PATH": "./.dev/secrets",
        "APP_RABBIT__DSN": "amqp://test:test@test:5672/",
    }

    with mock.patch.dict(os.environ, overrides):
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
        await conn.execute(sa.delete(sessions).where(sa.true()))
        await conn.execute(
            sa.delete(users).where(users.c.email != Email("root@svoifilm.com"))
        )
        await conn.execute(
            sa.delete(roles).where(
                roles.c.name.not_in(
                    [
                        "root",
                        "admin",
                        "viewer",
                        "content-owner",
                    ]
                )
            )
        )


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI]:
    from auth.api import create_app

    yield create_app()

    mapper_registry.dispose(cascade=True)


@pytest.fixture(scope="function")
def test_client(app: FastAPI) -> TestClient:
    return TestClient(app)
