from http import HTTPStatus
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine

from moderator.persistence.schema import moderators, moderation_requests


@pytest.mark.asyncio
async def test__moderator_and_moderation_request_flow__persists(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    response = test_client.post(
        "/moderators",
        headers={"Authorization": "Bearer admin-token"},
        json={
            "user": {
                "email": "moderator@example.com",
                "first_name": "Mod",
                "last_name": "Erator",
                "password": "secretpass",
            }
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    moderator_id = UUID(response.json()["id"])

    response = test_client.post(
        "/moderation-requests",
        headers={"Authorization": "Bearer content-owner-token"},
        json={
            "episode_id": "00000000-0000-0000-0000-000000000111",
            "content_owner_id": "00000000-0000-0000-0000-000000000222",
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    moderation_request_id = UUID(response.json()["id"])

    response = test_client.post(
        f"/moderation-requests/{moderation_request_id}/approve",
        headers={"Authorization": "Bearer moderator-token"},
        json={"moderator_id": str(moderator_id)},
    )
    assert response.status_code == HTTPStatus.OK, response.text
    body = response.json()
    assert body["moderator_id"] == str(moderator_id)
    assert body["status"] == "approved"

    async with engine.connect() as conn:
        moderators_total = await conn.scalar(
            sa.select(func.count()).select_from(moderators)
        )
        assert moderators_total == 1
        requests_total = await conn.scalar(
            sa.select(func.count()).select_from(moderation_requests)
        )
        assert requests_total == 1
