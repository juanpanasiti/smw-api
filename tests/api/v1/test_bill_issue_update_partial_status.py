"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_partial_status.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_status(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only status is changed to 'cancelled'.

    Verifies the status is updated and all other fields remain unchanged.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2025-06", amount="200.00", due_date="2025-06-15"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"status": "cancelled"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] == "cancelled"
    assert data["amount"] == "200.00"
    assert data["due_date"] == "2025-06-15"
    assert data["period"] == "2025-06"
