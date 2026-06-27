"""
Integration tests for DELETE /api/v1/bills/issues/{id}
and DELETE /api/v1/bills/services/{id}.

Covers the five scenarios specified in the task:
  1. Delete an issue OK
  2. Delete a service with no issues OK
  3. Delete a service with issues without ?force=true  → 409
  4. Delete a service with issues with ?force=true     → 204
  5. Force-delete with a simulated mid-delete failure  → service and issues still exist
"""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers (shared with other bill integration-test modules)
# ---------------------------------------------------------------------------


async def _create_category(client: AsyncClient, headers: dict) -> str:
    """Creates a movement category and returns its ID."""
    res = await client.post(
        "/api/v1/categories/",
        json={"name": f"Del Cat {uuid.uuid4()}", "is_income": False},
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _create_bill_service(client: AsyncClient, headers: dict, category_id: str) -> str:
    """Creates a bill service and returns its ID."""
    res = await client.post(
        "/api/v1/bills/services",
        json={
            "category_id": category_id,
            "name": f"Service {uuid.uuid4()}",
            "service_type": "utility",
            "expected_arrival_day": 10,
            "is_active": True,
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _create_bill_issue(
    client: AsyncClient,
    headers: dict,
    service_id: str,
    period: str = "2025-01",
    amount: str = "150.00",
    due_date: str = "2025-01-15",
) -> str:
    """Creates a bill issue and returns its ID."""
    res = await client.post(
        "/api/v1/bills/issues",
        json={
            "bill_service_id": service_id,
            "period": period,
            "amount": amount,
            "due_date": due_date,
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


# ---------------------------------------------------------------------------
# Scenario 1 — Delete an issue OK
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_issue_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Delete an existing bill issue.

    After a successful DELETE the issue must no longer appear in the issues list
    for its period.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(client, auth_headers, service_id, period="2027-01")

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


# ---------------------------------------------------------------------------
# Scenario 2 — Delete a service with no issues OK
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_no_issues_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Delete a bill service that has no associated issues.

    Verifies that the service is removed (GET /services no longer lists it) and
    the response status is 204.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

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


# ---------------------------------------------------------------------------
# Scenario 3 — Delete a service with issues without ?force=true → 409
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_with_issues_no_force(client: AsyncClient, auth_headers: dict) -> None:
    """
    Attempt to delete a service that has associated issues without the force flag.

    Verifies that the API returns 409 with the BILL_SERVICE_HAS_ISSUES error
    code, and that neither the service nor its issues are removed.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(client, auth_headers, service_id, period="2027-02")

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


# ---------------------------------------------------------------------------
# Scenario 4 — Delete a service with issues using ?force=true OK
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_with_issues_force_ok(client: AsyncClient, auth_headers: dict) -> None:
    """
    Force-delete a bill service that has associated issues.

    Verifies that both the service and all its issues are removed after a
    successful force-delete (204 response).
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id_a = await _create_bill_issue(client, auth_headers, service_id, period="2027-03")
    issue_id_b = await _create_bill_issue(client, auth_headers, service_id, period="2027-04")

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


# ---------------------------------------------------------------------------
# Scenario 5 — Force-delete with failure → service and issues intact (rollback)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_service_force_fail_rollback(client: AsyncClient, auth_headers: dict) -> None:
    """
    Force-delete triggered but a simulated failure mid-delete causes the
    operation to abort atomically; service and issues must remain intact.

    The test patches BillRepository.delete_service to raise a RuntimeError,
    simulating a database failure at the exact point where the DELETE statement
    would be flushed.  Since the exception is raised before any ``flush()``
    call, the SQLAlchemy session is never mutated: both the service and its
    issues remain in the database and are verifiable via subsequent GET requests.

    In the ASGI in-process test transport, unhandled RuntimeErrors propagate
    directly to the test caller (Starlette's server-error middleware is not
    active), so we capture the exception with ``pytest.raises`` and then assert
    data integrity with follow-up read requests.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(client, auth_headers, service_id, period="2027-05")

    async def _raise_on_delete(self, service):  # noqa: ANN001
        raise RuntimeError("Simulated database failure during delete_service")

    # The RuntimeError propagates to the test client in ASGI in-process mode.
    # We capture it here and then verify data integrity.
    with pytest.raises(RuntimeError, match="Simulated database failure during delete_service"):
        with patch(
            "src.repositories.bill_repository.BillRepository.delete_service",
            new=_raise_on_delete,
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
    issues_res = await client.get(
        "/api/v1/bills/issues", params={"period": "2027-05"}, headers=auth_headers
    )
    assert issues_res.status_code == 200
    remaining_issue_ids = [i["id"] for i in issues_res.json()["data"]]
    assert issue_id in remaining_issue_ids, "Issue must still exist after failed force-delete"

