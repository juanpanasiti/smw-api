"""
Associated Documentation: docs/integration_tests/test_bill_delete_issue_ok.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_issue_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Delete an existing bill issue.

    After a successful DELETE the issue must no longer appear in the issues list
    for its period.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(client, auth_headers, service_id, period="2027-01")

    res = await client.delete(
        f"/api/v1/bills/issues/{issue_id}",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 204, res.text

    # Verify the issue is gone: fetching issues for that period should return an empty list
    fetch_res = await client.get(
        "/api/v1/bills/issues",
        params={"period": "2027-01"},
        headers=auth_headers,
    )
    assert fetch_res.status_code == 200
    remaining_ids = [i["id"] for i in fetch_res.json()["data"]]
    assert issue_id not in remaining_ids
