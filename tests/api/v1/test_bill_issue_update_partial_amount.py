"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_partial_amount.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_amount(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only amount is changed.

    Verifies that non-provided fields retain their original values.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2025-05", amount="100.00", due_date="2025-05-10"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "999.50"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["amount"] == "999.50"
    assert data["period"] == "2025-05"
    assert data["due_date"] == "2025-05-10"
    assert data["status"] == "unpaid"
