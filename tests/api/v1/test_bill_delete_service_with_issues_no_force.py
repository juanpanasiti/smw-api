"""
Associated Documentation: docs/integration_tests/test_bill_delete_service_with_issues_no_force.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_with_issues_no_force(client: AsyncClient, auth_headers: dict) -> None:
    """
    Attempt to delete a service that has associated issues without the force flag.

    Verifies that the API returns 409 with the BILL_SERVICE_HAS_ISSUES error
    code, and that neither the service nor its issues are removed.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(client, auth_headers, service_id, period="2027-02")

    res = await client.delete(
        f"/api/v1/bills/services/{service_id}",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"]["error"]["code"] == "BILL_SERVICE_HAS_ISSUES"

    # The service must still exist
    list_res = await client.get("/api/v1/bills/services", headers=auth_headers)
    assert list_res.status_code == 200
    remaining_service_ids = [s["id"] for s in list_res.json()["data"]]
    assert service_id in remaining_service_ids

    # The issue must still exist
    issues_res = await client.get(
        "/api/v1/bills/issues", params={"period": "2027-02"}, headers=auth_headers
    )
    assert issues_res.status_code == 200
    remaining_issue_ids = [i["id"] for i in issues_res.json()["data"]]
    assert issue_id in remaining_issue_ids
