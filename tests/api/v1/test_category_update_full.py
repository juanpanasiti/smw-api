"""
Associated Documentation: docs/integration_tests/test_category_update_full.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_full(client: AsyncClient, auth_headers: dict):
    """
    Total update (3 fields): name, description, and is_income are updated simultaneously.
    """
    category_id = await create_category(client, auth_headers)

    update_res_total = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Updated Category", "description": "Updated description", "is_income": True},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_total.status_code == 200
    data = update_res_total.json()["data"]
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated description"
    assert data["is_income"] is True
