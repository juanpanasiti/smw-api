"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_partial_due_date.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_due_date(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only due_date is changed.

    Verifies that the due date is updated while all other fields remain intact.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2025-07", amount="50.00", due_date="2025-07-05"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"due_date": "2025-07-25"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["due_date"] == "2025-07-25"
    assert data["period"] == "2025-07"
    assert data["amount"] == "50.00"
    assert data["status"] == "unpaid"
