# Test Suite Documentation

This document describes every test in the suite, organized by type.
Each entry specifies: the **scenario** being exercised, the **input data** the test starts from, and the **expected result**.

## Infrastructure & Fixtures

All integration tests share a common fixture stack defined in [`conftest.py`](conftest.py):

| Fixture | Purpose |
|---|---|
| `db_session` | Async SQLAlchemy session wrapped in a transaction that is **rolled back** after each test, keeping the database clean. |
| `client` | HTTPX `AsyncClient` wired to the FastAPI ASGI app, with the real DB session injected via dependency override. |
| `auth_headers` | Registers a unique user and returns `Authorization: Bearer <token>` headers ready for authenticated requests. |
| `mock_redis_globally` | Auto-used monkeypatch that stubs every Redis call (`get`, `set`, `scan`, `delete`) with `AsyncMock`, preventing real cache side-effects during tests. |

Unit tests use local `AsyncMock` fixtures for each repository dependency — no database or HTTP server is involved.

---

## Unit Tests (`tests/unit/`)

### `test_security.py` — Core security utilities

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_password_hashing` | Hash a plain-text password and verify it | Plain password `"supersecretpassword123"` | Hash differs from the original string; `verify_password` returns `True` for the correct password and `False` for `"wrongpassword"` |
| 2 | `test_create_tokens` | Generate JWT access and refresh tokens | Subject string `"user123"` | Both `create_access_token` and `create_refresh_token` return non-empty strings |

---

### `test_config.py` — Application settings loading

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_settings_load_default` | Settings resolve to compiled defaults when no env vars are present | `POSTGRES_USER` removed from environment | `PROJECT_NAME == "Personal Finance API"`, `POSTGRES_USER == "postgres"`, `API_V1_STR == "/api/v1"` |
| 2 | `test_settings_custom_env` | Settings pick up custom environment variables via `monkeypatch` | `POSTGRES_USER="test_user"`, `POSTGRES_PASSWORD="test_pass"` | Settings reflect the overridden values; `async_database_url` contains `"test_user:test_pass"` |

---

### `test_core.py` — Database and Redis dependency generators

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_get_db_session` | `get_db_session` yields a usable async DB session | No arguments | The yielded object is an instance of `AsyncSession` |
| 2 | `test_get_redis_client` | `get_redis_client` yields a non-null Redis client | No arguments | The yielded client is not `None` |

---

### `test_auth.py` — `AuthService` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_register_user_success` | Register a new user when the email is not taken | `email="test@example.com"`, full profile with `monthly_spending_limit=1000.00` | User returned with correct email and first name; repository `create` called once |
| 2 | `test_register_user_existing_email` | Attempt registration with an already-registered email | Same schema as above; repo mock returns an existing `User` | `ValueError` raised with code `EMAIL_ALREADY_REGISTERED` |
| 3 | `test_login_user_success` | Login with correct credentials | Email + matching plain-text password against a bcrypt hash | Returns a token pair with non-null `access_token` and `refresh_token` |
| 4 | `test_login_user_invalid_password` | Login with wrong password | Email with correct hash in repo; password `"wrongpassword"` | `ValueError` raised with code `INVALID_CREDENTIALS` |

---

### `test_account.py` — `AccountService` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_get_user_accounts` | Retrieve all accounts for a user | Repo mock returns one `CreditCard` for a given `owner_id` | List of length 1 returned; `get_all_for_owner` called once with the correct `owner_id` |
| 2 | `test_create_credit_card` | Create a new credit card | `alias="Visa Gold"`, `closing_day=10`, `due_day=20`, `limit=5000.00`, `financing_limit=2500.00` | Returned card has the expected alias, correct `owner_id`, and `limit == Decimal("5000.00")`; repo `create` called once |
| 3 | `test_create_extension_card_forbidden` | Try to create an extension card under a parent owned by a different user | Parent card in repo belongs to `other_owner_id`; request from `owner_id` with `main_credit_card_id` pointing to that parent | `ValueError` raised with code `PARENT_CARD_NOT_FOUND_OR_FORBIDDEN` |
| 4 | `test_delete_account_forbidden` | Try to delete an account that belongs to another user | Repo returns a card owned by `other_owner_id` | `ValueError` raised with code `FORBIDDEN_ACCOUNT` |
| 5 | `test_update_credit_card_not_found` | Try to update a credit card that does not exist | `get_credit_card_by_id` returns `None` | `ValueError` raised with code `ACCOUNT_NOT_FOUND` |

---

### `test_category.py` — `MovementCategoryService` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_get_user_categories` | Retrieve all categories visible to a user (global + own) | Repo returns one global category (`user_id=None`) and one user-specific category | List of length 2; `get_all_for_user` called once |
| 2 | `test_create_category` | Create a new expense category | `name="Groceries"`, `description="Food expenses"`, `is_income=False` | Category returned with correct name and `user_id`; repo `create` called once |
| 3 | `test_delete_category_success` | Delete a category owned by the requesting user | Repo returns a category with matching `user_id` | No exception raised; `delete` called once |
| 4 | `test_delete_category_forbidden` | Try to delete a global category or one belonging to another user | ① Global category (`user_id=None`); ② Category belonging to `other_user_id` | `ValueError` raised with code `FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY` in both cases |

---

### `test_bill.py` — `BillServiceManager` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_create_service` | Create a new bill service (e.g., internet subscription) | `name="Internet"`, `service_type="internet"`, `expected_arrival_day=15`, `is_active=True` | Returned service has correct `name` and `user_id`; repo `create_service` called once |
| 2 | `test_create_issue_duplicate_period` | Try to register a bill issue for a period that already has one | Repo mock returns an existing `BillIssue` for the same `bill_service_id` and `period="2026-06"` | `HTTPException` with status `409` raised |
| 3 | `test_pay_issue_success` | Pay an unpaid bill issue and auto-generate its expense | Unpaid `BillIssue` with `amount=50.00`; `BillIssuePaySchema` with an `account_id` | Issue status changes to `"paid"`, `expense_id` is set; `create_purchase` called with `amount=50.00`, `total_installments=1`, correct `account_id` and `category_id` |

---

### `test_expense.py` — `ExpenseService` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_create_purchase` | Create a purchase and auto-generate split installment payments | `title="New Laptop"`, `amount=1200.00`, `total_installments=3`, `first_payment_date=2026-07-20` | Purchase returned with correct title and 3 installments; `create_payments` called with a list of 3 payments each with `amount=400.00`; first payment has `period_month=7, period_year=2026`; last payment has `is_last_payment=True` |
| 2 | `test_optimistic_locking_payment` | Enforce optimistic locking on payment status updates | ① `version_id=999` (stale) vs. current `version_id=1`; ② retry with correct `version_id=1` and `status="paid"` | ① `HTTPException` with status `409`; ② Payment status updated to `"paid"` and repo `update_payment` called once |

---

## Integration Tests (`tests/api/v1/`)

> All integration tests run against a real PostgreSQL test database (`smw_api_test` on port `5433`).
> Every test is wrapped in a transaction that is rolled back at teardown, ensuring full isolation.

---

### `test_auth.py` — Authentication endpoints

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_auth_registration_and_login` | Register a new user and then log in | `POST /api/v1/auth/register` with unique email, password `"Password123!"`, full profile (`monthly_spending_limit=5000.00`); then `POST /api/v1/auth/login` | Registration returns `201` with `email` and `role="user"` in response; login returns `200` with `access_token` and `refresh_token` |
| 2 | `test_auth_refresh_token` | Refresh a valid token and reject an invalid one | ① `POST /api/v1/auth/refresh` with a valid `refresh_token` obtained from login; ② same endpoint with `"invalid_token_string"` | ① Returns `200` with new `access_token` and `refresh_token`; ② Returns `401` with error code `INVALID_REFRESH_TOKEN` |

---

### `test_bill_service_update.py` — `PATCH /api/v1/bills/services/{id}`

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_bill_service_update_full` | Full update — all five fields sent at once | Existing service (type `utility`, arrival day `10`, active); payload with new `category_id`, `name="Electricity Updated"`, `service_type="electric"`, `expected_arrival_day=20`, `is_active=False` | `200` response; all five fields reflect the new values |
| 2 | `test_bill_service_update_partial` | Partial update — only `name` and `is_active` changed | Payload `{"name": "Partial Name", "is_active": false}` | `200`; updated fields match; `service_type`, `expected_arrival_day`, and `category_id` remain at their original values |
| 3 | `test_bill_service_update_empty_body_returns_422` | Empty body sent — at least one field required | `PATCH` with `{}` | `422` response; body contains `"At least one field must be provided for update"` |
| 4 | `test_bill_service_update_not_found_returns_404` | Update a service that does not exist | Random UUID as service ID | `404` with error code `BILL_SERVICE_NOT_FOUND` |
| 5 | `test_bill_service_update_other_user_returns_404` | User B tries to update a service owned by User A | User A creates service; User B authenticates separately and sends a `PATCH` on that service ID | `404` with error code `BILL_SERVICE_NOT_FOUND` (ownership leak prevented by returning 404 instead of 403) |

---

### `test_bill_issue_update.py` — `PATCH /api/v1/bills/issues/{id}`

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_bill_issue_update_full` | Full update — all four fields changed at once | Existing issue (`period="2025-03"`, `amount=150.00`); payload with `amount=299.99`, `due_date=2025-03-20`, `period=2025-04`, `status=cancelled` | `200`; all four fields reflect the new values |
| 2 | `test_bill_issue_update_partial_amount` | Partial update — only `amount` changed | Existing issue (`period="2025-05"`, `amount=100.00`, `due_date=2025-05-10`); payload `{"amount": "999.50"}` | `200`; `amount=999.50`; `period`, `due_date`, and `status` remain unchanged |
| 3 | `test_bill_issue_update_partial_status` | Partial update — only `status` changed to `cancelled` | Existing issue (`period="2025-06"`, `amount=200.00`); payload `{"status": "cancelled"}` | `200`; `status=cancelled`; all other fields unchanged |
| 4 | `test_bill_issue_update_partial_due_date` | Partial update — only `due_date` changed | Existing issue (`period="2025-07"`, `amount=50.00`, `due_date=2025-07-05`); payload `{"due_date": "2025-07-25"}` | `200`; `due_date=2025-07-25`; all other fields unchanged |
| 5 | `test_bill_issue_update_partial_period` | Partial update — period moved to a free slot | Existing issue at `period="2025-08"`; payload `{"period": "2025-09"}` (unoccupied) | `200`; `period=2025-09`; amount and status unchanged |
| 6 | `test_bill_issue_update_empty_body_returns_422` | Empty body — at least one field required | `PATCH` with `{}` | `422`; body contains `"At least one field must be provided for update"` |
| 7 | `test_bill_issue_update_paid_returns_409` | Attempt to modify an issue that is already `paid` | Issue forced to `status=paid` via a prior PATCH; then new PATCH with `amount=999.00` | `409` with error code `BILL_ISSUE_ALREADY_PAID` |
| 8 | `test_bill_issue_update_period_conflict_returns_409` | Target period already occupied by another issue of the same service | Two issues created for `2026-01` and `2026-02`; attempt to move the first to `2026-02` | `409` with error code `BILL_ISSUE_PERIOD_CONFLICT` |
| 9 | `test_bill_issue_update_not_found_returns_404` | Update an issue that does not exist | Random UUID as issue ID | `404` |
| 10 | `test_bill_issue_update_other_user_returns_404` | User B tries to update an issue owned by User A | User A creates category → service → issue; User B authenticates separately and sends PATCH on that issue ID | `404` (ownership leak prevented) |

---

### `test_category_update.py` — `PATCH /api/v1/categories/{id}`

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_category_update_scenarios` — **Full update** | All three fields updated simultaneously | `name="Updated Category"`, `description="Updated description"`, `is_income=True` | `200`; all three fields reflect the new values |
| 2 | `test_category_update_scenarios` — **Partial update** | Only `name` changed | `{"name": "Partially Updated Category"}` on the previously updated category | `200`; name changes; `description` and `is_income` remain from the prior update |
| 3 | `test_category_update_scenarios` — **Empty payload** | Empty body rejected by schema validator | `PATCH` with `{}` | `422`; body contains `"At least one field must be provided for update"` |
| 4 | `test_category_update_with_expenses` — **`is_income` blocked by associated expenses** | Changing `is_income` on a category that already has expenses linked to it | Category with a purchase of `1200.00` (3 installments) attached; payload `{"is_income": true}` | `400` with error code `CATEGORY_HAS_EXPENSES` and message `"Cannot update is_income because there are expenses associated with this category."` |
| 5 | `test_category_update_with_expenses` — **Other fields allowed despite expenses** | Changing `name` on a category that has expenses | Payload `{"name": "New Name"}` on the same category that has purchases | `200` — non-`is_income` fields remain updatable |
| 6 | `test_category_update_permissions` — **Cross-user modification blocked** | User 2 attempts to update a category owned by User 1 | User 2 authenticated; `PATCH` on User 1's `category_id` with `{"name": "Hacked"}` | `403` with error code `FORBIDDEN_OPERATION` |

---

### `test_projections.py` — `GET /api/v1/projections/periods/{period}`

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_projection_end_to_end` | Full end-to-end flow: create card → register installment purchase → query monthly projection | Credit card with `limit=5000.00`; purchase of `amount=1200.00` split into 3 installments starting next month | Projection for the first installment month returns `total_expenses="400.00"` and a payments list with at least one entry where `amount="400.00"` (i.e., `1200 / 3`) |
