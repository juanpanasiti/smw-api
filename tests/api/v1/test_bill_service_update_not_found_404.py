"""
Associated Documentation: docs/integration_tests/test_bill_service_update_not_found_404.md
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_not_found_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Non-existent service ID.

    Verifies that attempting to update a service that does not exist returns
    404 with the BILL_SERVICE_NOT_FOUND error code.
    """
    non_existent_id = uuid.uuid4()

    res = await client.patch(
        f"/api/v1/bills/services/{non_existent_id}",
        json={"name": "Ghost Service"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
    assert res.json()["detail"]["error"]["code"] == "BILL_SERVICE_NOT_FOUND"
