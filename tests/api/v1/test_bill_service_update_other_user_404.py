"""
Associated Documentation: docs/integration_tests/test_bill_service_update_other_user_404.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_service, create_category, register_and_login


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_other_user_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Cross-user access: user B tries to update a service owned by user A.

    Verifies that the ownership check returns 404 (not 403) to avoid leaking
    information about resource existence.
    """
    # User A creates a service
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)

    # User B registers and logs in
    user_b_headers = await register_and_login(client)

    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={"name": "Hijacked"},
        headers={**user_b_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
    assert res.json()["detail"]["error"]["code"] == "BILL_SERVICE_NOT_FOUND"
