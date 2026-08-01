"""
Associated Documentation: docs/integration_tests/test_bill_service_update_full.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_full(client: AsyncClient, auth_headers: dict):
    """
    Full update: all five updatable fields are sent in the request body.

    Verifies that every field is persisted and returned correctly in the response.
    """
    category_id = await create_category(client, auth_headers)
    new_category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)

    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={
            "category_id": new_category_id,
            "name": "Electricity Updated",
            "service_type": "electric",
            "expected_arrival_day": 20,
            "is_active": False,
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["id"] == service_id
    assert data["category_id"] == new_category_id
    assert data["name"] == "Electricity Updated"
    assert data["service_type"] == "electric"
    assert data["expected_arrival_day"] == 20
    assert data["is_active"] is False
