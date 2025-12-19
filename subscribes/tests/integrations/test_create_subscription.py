from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine

from subscriptions.persistence.schema import subscriptions


@pytest.mark.asyncio
async def test__create_subscription__persists(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    response = test_client.post(
        "/subscriptions",
        json={
            "level": "L",
            "expires_at": expires_at,
        },
    )
    assert response.status_code == HTTPStatus.CREATED, await response.aread()
    body = response.json()
    assert body["level"] == "L"

    async with engine.connect() as conn:
        total = await conn.scalar(sa.select(func.count()).select_from(subscriptions))
        assert total == 1
