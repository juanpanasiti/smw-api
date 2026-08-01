"""
Associated Documentation: docs/integration_tests/test_bill_delete_service_force_fail_rollback.md
"""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_force_fail_rollback(client: AsyncClient, auth_headers: dict) -> None:
    """
    Force-delete triggered but a simulated failure mid-delete causes the
    operation to abort atomically; service and issues must remain intact.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(client, auth_headers, service_id, period="2027-05")

    async def _raise_on_delete(self, service):  # noqa: ANN001, ARG001
        raise RuntimeError("Simulated database failure during delete_service")

    with (
        pytest.raises(RuntimeError, match="Simulated database failure during delete_service"),
        patch(
            "src.repositories.bill_repository.BillRepository.delete_service",
            new=_raise_on_delete,
        ),
    ):
        await client.delete(
            f"/api/v1/bills/services/{service_id}",
            params={"force": "true"},
            headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        )

    # No flush occurred before the exception, so the service must still exist.
    list_res = await client.get("/api/v1/bills/services", headers=auth_headers)
    assert list_res.status_code == 200
    remaining_service_ids = [s["id"] for s in list_res.json()["data"]]
    assert service_id in remaining_service_ids, "Service must still exist after failed force-delete"

    # The issue must also still exist — the transaction was never committed.
    issues_res = await client.get("/api/v1/bills/issues", params={"period": "2027-05"}, headers=auth_headers)
    assert issues_res.status_code == 200
    remaining_issue_ids = [i["id"] for i in issues_res.json()["data"]]
    assert issue_id in remaining_issue_ids, "Issue must still exist after failed force-delete"
