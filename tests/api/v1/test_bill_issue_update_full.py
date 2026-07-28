"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_full.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_full(client: AsyncClient, auth_headers: dict):
    """
    Full update: all four updatable fields are sent in a single request.

    Verifies that every field is persisted and returned correctly in the response.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(client, auth_headers, service_id, period="2025-03")

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={
            "amount": "299.99",
            "due_date": "2025-03-20",
            "period": "2025-04",
            "status": "cancelled",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["id"] == issue_id
    assert data["amount"] == "299.99"
    assert data["due_date"] == "2025-03-20"
    assert data["period"] == "2025-04"
    assert data["status"] == "cancelled"
