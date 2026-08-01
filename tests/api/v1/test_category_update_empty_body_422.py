"""
Associated Documentation: docs/integration_tests/test_category_update_empty_body_422.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_empty_body_422(client: AsyncClient, auth_headers: dict):
    """
    Empty payload: passing {} returns 422 validation error.
    """
    category_id = await create_category(client, auth_headers)

    update_res_empty = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_empty.status_code == 422
    assert "At least one field must be provided for update" in update_res_empty.text
