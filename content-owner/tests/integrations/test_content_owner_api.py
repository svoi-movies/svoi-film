from http import HTTPStatus
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine

from content_owner.persistence.schema import content_owners


@pytest.mark.asyncio
async def test__create_content_owner__persists(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    company_id = UUID("00000000-0000-0000-0000-000000000abc")
    response = test_client.post(
        "/content-owners",
        headers={"Authorization": "Bearer moderator-token"},
        json={
            "user": {
                "email": "owner@example.com",
                "first_name": "Olga",
                "last_name": "Owner",
                "password": "secretpass",
            },
            "company_id": str(company_id),
            "permissions": ["upload_titles", "edit_titles"],
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    body = response.json()
    assert body["company_id"] == str(company_id)
    assert body["permissions"] == ["upload_titles", "edit_titles"]
    assert body["user_id"] == "00000000-0000-0000-0000-000000000999"

    async with engine.connect() as conn:
        total = await conn.scalar(sa.select(func.count()).select_from(content_owners))
        assert total == 1
