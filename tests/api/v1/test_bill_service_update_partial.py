"""
Associated Documentation: docs/integration_tests/test_bill_service_update_partial.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_partial(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only a subset of fields is sent.

    Verifies that only the provided fields change while the rest retain their
    original values.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)

    # Update only name and is_active
    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={"name": "Partial Name", "is_active": False},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["name"] == "Partial Name"
    assert data["is_active"] is False
    # Fields not included in the request must remain unchanged
    assert data["service_type"] == "utility"
    assert data["expected_arrival_day"] == 10
    assert data["category_id"] == category_id
