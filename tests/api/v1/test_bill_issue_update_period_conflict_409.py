"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_period_conflict_409.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_period_conflict_returns_409(client: AsyncClient, auth_headers: dict):
    """
    Period conflict: the target period is already used by another issue of the same service.

    Verifies that the service rejects the update with 409 and the
    BILL_ISSUE_PERIOD_CONFLICT error code.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)

    # Create two issues for the same service in different periods
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2026-01", amount="100.00", due_date="2026-01-15"
    )
    await create_bill_issue(
        client, auth_headers, service_id, period="2026-02", amount="100.00", due_date="2026-02-15"
    )

    # Attempt to move issue_id to 2026-02, which is already taken
    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"period": "2026-02"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "BILL_ISSUE_PERIOD_CONFLICT"
