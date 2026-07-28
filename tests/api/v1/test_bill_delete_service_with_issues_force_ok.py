"""
Associated Documentation: docs/integration_tests/test_bill_delete_service_with_issues_force_ok.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_with_issues_force_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Force-delete a bill service that has associated issues.

    Verifies that both the service and all its issues are removed after a
    successful force-delete (204 response).
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id_a = await create_bill_issue(client, auth_headers, service_id, period="2027-03")
    issue_id_b = await create_bill_issue(client, auth_headers, service_id, period="2027-04")

    res = await client.delete(
        f"/api/v1/bills/services/{service_id}",
        params={"force": "true"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 204, res.text

    # The service must be gone
    list_res = await client.get("/api/v1/bills/services", headers=auth_headers)
    assert list_res.status_code == 200
    remaining_service_ids = [s["id"] for s in list_res.json()["data"]]
    assert service_id not in remaining_service_ids

    # All issues must be gone (cascade)
    for period, issue_id in [("2027-03", issue_id_a), ("2027-04", issue_id_b)]:
        issues_res = await client.get(
            "/api/v1/bills/issues", params={"period": period}, headers=auth_headers
        )
        assert issues_res.status_code == 200
        remaining_issue_ids = [i["id"] for i in issues_res.json()["data"]]
        assert issue_id not in remaining_issue_ids
