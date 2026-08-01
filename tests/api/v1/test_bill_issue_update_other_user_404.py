"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_other_user_404.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category, register_and_login


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_other_user_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Cross-user access: user B tries to update a bill issue owned by user A.

    Verifies that the ownership check returns 404 (not 403) to avoid leaking
    information about resource existence.
    """
    # User A creates a service and an issue
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(
        client, auth_headers, service_id, period="2026-03", amount="80.00", due_date="2026-03-10"
    )

    # User B registers and logs in
    user_b_headers = await register_and_login(client)

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "1.00"},
        headers={**user_b_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
