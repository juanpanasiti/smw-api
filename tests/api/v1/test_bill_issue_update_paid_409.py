"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_paid_409.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_paid_returns_409(client: AsyncClient, auth_headers: dict):
    """
    Paid-issue guard: attempt to update a bill issue that is in 'paid' status.

    Verifies that the service rejects the request with 409 and the
    BILL_ISSUE_ALREADY_PAID error code.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2025-11", amount="120.00", due_date="2025-11-15"
    )

    # Force the issue into 'paid' status via a direct partial update
    force_res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"status": "paid"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert force_res.status_code == 200, force_res.text

    # Now attempt to modify the already-paid issue
    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "999.00"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "BILL_ISSUE_ALREADY_PAID"
