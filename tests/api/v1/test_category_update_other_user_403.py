"""
Associated Documentation: docs/integration_tests/test_category_update_other_user_403.md
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_category, register_and_login


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_permissions(client: AsyncClient, auth_headers: dict):
    """
    Cross-user modification: User 2 attempts to update User 1's category, returning 403.
    """
    user2_headers = await register_and_login(client)
    category_id = await create_category(client, auth_headers)

    # User 2 tries to update User 1's category (expect 403)
    update_res_403 = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Hacked"},
        headers={**user2_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_403.status_code == 403
    assert update_res_403.json()["detail"]["error"]["code"] == "FORBIDDEN_OPERATION"
