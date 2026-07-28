"""
Associated Documentation: docs/integration_tests/test_bill_issue_update_empty_body_422.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_bill_issue, create_bill_service, create_category


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_empty_body_returns_422(client: AsyncClient, auth_headers: dict):
    """
    Empty body: no fields are provided.

    Verifies that Pydantic's @model_validator rejects the request with 422
    and includes the expected validation message.
    """
    category_id = await create_category(client, auth_headers)
    service_id = await create_bill_service(client, auth_headers, category_id)
    issue_id = await create_bill_issue(client, auth_headers, service_id, period="2025-10")

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 422, res.text
    assert "At least one field must be provided for update" in res.text
