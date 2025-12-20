from http import HTTPStatus
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine

from company.persistence.schema import companies, content_owners


@pytest.mark.asyncio
async def test__create_company_and_add_content_owner__persists(
    clean_tables: None,
    test_client: TestClient,
    engine: AsyncEngine,
) -> None:
    response = test_client.post(
        "/companies",
        headers={"Authorization": "Bearer admin-token"},
        json={"name": "Svoi Film"},
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    company_id = UUID(response.json()["id"])

    response = test_client.post(
        f"/companies/{company_id}/content-owners",
        headers={"Authorization": "Bearer admin-token"},
        json={
            "user": {
                "email": "owner@example.com",
                "first_name": "Olga",
                "last_name": "Owner",
                "password": "secretpass",
            },
            "permissions": ["upload_titles", "edit_titles"],
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    body = response.json()
    assert body["company_id"] == str(company_id)
    assert body["permissions"] == ["upload_titles", "edit_titles"]
    assert body["user_id"] == "00000000-0000-0000-0000-000000000999"

    async with engine.connect() as conn:
        companies_total = await conn.scalar(
            sa.select(func.count()).select_from(companies)
        )
        assert companies_total == 1
        total = await conn.scalar(sa.select(func.count()).select_from(content_owners))
        assert total == 1
