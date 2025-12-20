from http import HTTPStatus

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import functions as f

from payments.persistence.schema import users


@pytest.mark.asyncio
async def test__create_viewer__can_create_valid_viewer(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    response = test_client.post(
        "/users/viewer",
        json={
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "Abacaba!23",
        },
    )
    assert response.status_code == HTTPStatus.OK, await response.aread()

    async with engine.connect() as conn:
        await conn.execute(sa.select(f.count(1)).select_from(users))
