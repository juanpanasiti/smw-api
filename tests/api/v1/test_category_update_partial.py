"""
Associated Documentation: docs/integration_tests/test_category_update_partial.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_partial(client: AsyncClient, auth_headers: dict):
    """
    Partial update (1 field): only name is updated, unmentioned fields remain intact.
    """
    category_id = await create_category(client, auth_headers)

    update_res_partial = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Partially Updated Category"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_partial.status_code == 200
    data = update_res_partial.json()["data"]
    assert data["name"] == "Partially Updated Category"
    assert data["is_income"] is False
