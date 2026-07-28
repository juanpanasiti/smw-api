"""
Associated Documentation: docs/integration_tests/test_bill_delete_service_no_issues_ok.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_no_issues_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Delete a bill service that has no associated issues.

    Verifies that the service is removed (GET /services no longer lists it) and
    the response status is 204.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)

    res = await client.delete(
        f"/api/v1/bills/services/{service_id}",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 204, res.text

    # Verify the service is gone
    list_res = await client.get("/api/v1/bills/services", headers=auth_headers)
    assert list_res.status_code == 200
    remaining_ids = [s["id"] for s in list_res.json()["data"]]
    assert service_id not in remaining_ids
