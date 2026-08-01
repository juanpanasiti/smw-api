"""
Shared helper functions for integration tests in tests/api/v1/
"""

import datetime
import uuid

from httpx import AsyncClient


async def create_category(client: AsyncClient, headers: dict) -> str:
    """Creates a movement category and returns its ID."""
    res = await client.post(
        "/api/v1/categories/",
        json={"name": f"Category {uuid.uuid4()}", "is_income": False},
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def create_bill_service(client: AsyncClient, headers: dict, category_id: str) -> str:
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


async def create_bill_issue(
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


async def create_credit_card(client: AsyncClient, headers: dict) -> str:
    """Creates a credit card account and returns its ID."""
    res = await client.post(
        "/api/v1/accounts/credit-cards",
        json={
            "alias": f"Card {uuid.uuid4()}",
            "closing_day": 1,
            "due_day": 10,
            "limit": "5000.00",
            "financing_limit": "2500.00",
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def register_and_login(client: AsyncClient) -> dict:
    """Registers a new user and returns auth headers with Bearer token."""
    uid = uuid.uuid4()
    email = f"user_{uid}@test.com"
    password = "Password123!"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "profile": {
                "first_name": "Test",
                "last_name": "User",
                "birthdate": "1990-01-01",
                "monthly_spending_limit": "2000.00",
            },
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def next_month_date() -> datetime.date:
    """Returns a date in the 10th day of next month."""
    today = datetime.date.today()
    first_of_next = today.replace(day=1) + datetime.timedelta(days=32)
    return first_of_next.replace(day=10)
