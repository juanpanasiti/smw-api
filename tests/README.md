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

### `test_bill_delete.py` — `BillServiceManager` delete business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_delete_issue_success` | Delete an existing issue belonging to the requesting user | `BillIssue` and `BillService` both owned by `user_id` | No exception; repo `delete_issue` called once with the issue |
| 2 | `test_delete_issue_not_found` | Attempt to delete an issue that does not exist | `get_issue_by_id` returns `None` | `HTTPException` with status `404` raised |
| 3 | `test_delete_issue_other_user` | Attempt to delete an issue owned by a different user | Issue's `bill_service.user_id` differs from `requesting_user_id` | `HTTPException` with status `404` raised (ownership leak prevented) |
| 4 | `test_delete_service_no_issues_success` | Delete a service that has no associated issues | `get_issues_by_service` returns `[]` | No exception; repo `delete_service` called once |
| 5 | `test_delete_service_with_issues_no_force` | Attempt to delete a service with issues without `force=True` | `get_issues_by_service` returns one `BillIssue`; `force=False` | `ValueError("BILL_SERVICE_HAS_ISSUES")` raised; `delete_service` never called |
| 6 | `test_delete_service_with_issues_force` | Delete a service with issues using `force=True` | `force=True`; one linked `BillIssue` exists in repo mock | No exception; `get_issues_by_service` skipped; `delete_service` called once |
| 7 | `test_delete_service_not_found` | Attempt to delete a non-existent service | `get_service_by_id` returns `None` | `ValueError("BILL_SERVICE_NOT_FOUND")` raised; `delete_service` never called |

---

### `test_expense.py` — `ExpenseService` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_create_purchase` | Create a purchase and auto-generate split installment payments | `title="New Laptop"`, `amount=1200.00`, `total_installments=3`, `first_payment_date=2026-07-20` | Purchase returned with correct title and 3 installments; `create_payments` called with a list of 3 payments each with `amount=400.00`; first payment has `period_month=7, period_year=2026`; last payment has `is_last_payment=True` |
| 2 | `test_optimistic_locking_payment` | Enforce optimistic locking on payment status updates | ① `version_id=999` (stale) vs. current `version_id=1`; ② retry with correct `version_id=1` and `status="paid"` | ① `HTTPException` with status `409`; ② Payment status updated to `"paid"` and repo `update_payment` called once |

---

### `test_expense_delete.py` — `ExpenseService` delete business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_delete_expense_success` | Delete an existing expense belonging to the requesting user | Valid expense and account owned by user | No exception; repo `delete` called once with the expense |
| 2 | `test_delete_expense_not_found` | Attempt to delete an expense that does not exist | `get_by_id` returns `None` | `HTTPException` with status `404` raised |
| 3 | `test_delete_expense_unauthorized` | Attempt to delete an expense owned by a different user | Expense's `account.owner_id` differs from `requesting_user_id` | `HTTPException` with status `404` raised |

---

### `test_expense_payment_creation.py` — `ExpenseService.create_expense_payment` business logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_create_expense_payment_expense_not_found` | Expense ID does not exist in the database | Random `expense_id`; valid `SubscriptionPaymentCreateSchema` | `HTTPException` with status `404` raised |
| 2 | `test_create_expense_payment_wrong_owner` | Expense exists but the account belongs to a different user | Valid subscription; `Account.owner_id` set to a different `user_id` | `HTTPException` with status `404` raised (ownership check via `_verify_account_ownership`) |
| 3 | `test_create_expense_payment_unsupported_type` | Expense is a `purchase`, which does not support manual payment creation | Valid purchase expense owned by the requesting user; valid payment schema | `HTTPException` with status `400`; `detail.code == "EXPENSE_TYPE_DOES_NOT_SUPPORT_PAYMENTS"` |
| 4 | `test_create_expense_payment_updates_subscription_amount` | New payment is the most recent one for the subscription | Subscription with `amount=15.00`; new payment for `2026-07` with `amount=18.99`; `get_latest_payment_for_expense` returns the newly created payment | Payment created successfully; `update_expense` called once; `subscription.amount` updated to `18.99` |
| 5 | `test_create_expense_payment_does_not_update_amount_when_posterior_exists` | A later payment already exists for the subscription | New payment for `2026-05` with `amount=14.99`; latest payment in DB is for `2026-07` | Payment created successfully; `update_expense` NOT called; `subscription.amount` remains unchanged |

---

### `test_expense_payment_amount_update.py` — `ExpenseService.update_payment` amount redistribution logic

| # | Test function | Scenario | Input data | Expected result |
|---|---|---|---|---|
| 1 | `test_update_payment_payment_not_found` | Target payment does not exist | Random `payment_id` | `HTTPException 404` |
| 2 | `test_update_payment_wrong_owner` | Payment belongs to an account owned by a different user | Valid payment; `Account.owner_id` differs | `HTTPException 404` |
| 3 | `test_update_payment_amount_not_allowed_for_subscription` | Try to update the amount of a Subscription payment (not allowed) | Payment belonging to a Subscription expense; new amount provided | `HTTPException 400` with code `EXPENSE_TYPE_DOES_NOT_SUPPORT_AMOUNT_UPDATE` |
| 4 | `test_update_payment_optimistic_lock_conflict` | Version mismatch during update | Request `version_id` differs from DB `version_id` | `HTTPException 409` |
| 5 | `test_update_payment_amount_exceeds_purchase_total` | New amount combined with locked siblings exceeds the purchase total | Purchase=100; locked_sum=70; new amount=40 | `HTTPException 422` with code `PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL` |
| 6 | `test_update_payment_amount_exact_redistribution` | Exact redistribution across remaining unconfirmed siblings | Purchase=1200/3 installments; change #1 from 400 to 500 | Remaining budget 700 distributed exactly as [350, 350] |
| 7 | `test_update_payment_amount_non_divisible_redistribution` | Redistribution with remainder (decremental balance algorithm) | Purchase=100/3 installments; change #1 from 33.33 to 33.35 | Remaining budget 66.65 distributed as [33.32, 33.33] (due to banker's rounding) |
| 8 | `test_update_payment_amount_with_locked_payments` | Locked payments (paid/confirmed) are excluded from the redistribution pool | Purchase=100/3; #3 is locked (33.33); change #1 to 40.00 | Remaining 26.67 assigned entirely to #2; #3 remains 33.33 |
| 9 | `test_update_payment_same_amount_no_redistribution` | Request amount is identical to the current DB amount | `data.amount == payment.amount` | Scalar update applies immediately without triggering the redistribution logic array |

## Integration Tests (`tests/api/v1/`)

> All integration tests run against a real PostgreSQL test database (`smw_api_test` on port `5433`).
> Every test is wrapped in a transaction that is rolled back at teardown, ensuring full isolation.
> Every single test scenario under `tests/api/v1/` resides in its own isolated Python test file and has a 1-to-1 Markdown specification document in `docs/integration_tests/` matching its exact filename (1 scenario = 1 `.py` file ↔ 1 `.md` spec file). All tests and specifications are written strictly in English.
> Shared helper functions are located in `tests/api/v1/helpers.py`.

---

### Authentication Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_auth_registration_and_login.py` | `test_auth_registration_and_login.md` | Register a new user and log in | Registration returns `201`; login returns `200` with JWT access & refresh tokens |
| `test_auth_refresh_token.py` | `test_auth_refresh_token.md` | Refresh a valid token and reject invalid tokens | Valid refresh returns `200` with new tokens; invalid token returns `401 INVALID_REFRESH_TOKEN` |

---

### Bill Service & Issue Deletion Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_bill_delete_issue_ok.py` | `test_bill_delete_issue_ok.md` | Delete an existing bill issue | Returns `204`; issue no longer listed in period queries |
| `test_bill_delete_service_no_issues_ok.py` | `test_bill_delete_service_no_issues_ok.md` | Delete a service with no associated issues | Returns `204`; service no longer listed |
| `test_bill_delete_service_with_issues_no_force.py` | `test_bill_delete_service_with_issues_no_force.md` | Attempt to delete service with issues without `?force=true` | Returns `409 BILL_SERVICE_HAS_ISSUES`; service and issues remain intact |
| `test_bill_delete_service_with_issues_force_ok.py` | `test_bill_delete_service_with_issues_force_ok.md` | Force-delete a service with issues using `?force=true` | Returns `204`; service and child issues cascade deleted |
| `test_bill_delete_service_force_fail_rollback.py` | `test_bill_delete_service_force_fail_rollback.md` | Force-delete failure atomicity check | Exception caught; DB transaction rolled back; service and issues persist |

---

### Bill Issue Update Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_bill_issue_update_full.py` | `test_bill_issue_update_full.md` | Full update (amount, due_date, period, status) | Returns `200`; all four fields updated |
| `test_bill_issue_update_partial_amount.py` | `test_bill_issue_update_partial_amount.md` | Partial update (amount only) | Returns `200`; amount updated; other fields unchanged |
| `test_bill_issue_update_partial_status.py` | `test_bill_issue_update_partial_status.md` | Partial update (status to cancelled) | Returns `200`; status updated |
| `test_bill_issue_update_partial_due_date.py` | `test_bill_issue_update_partial_due_date.md` | Partial update (due_date only) | Returns `200`; due date updated |
| `test_bill_issue_update_partial_period.py` | `test_bill_issue_update_partial_period.md` | Partial update (period to free slot) | Returns `200`; period updated |
| `test_bill_issue_update_empty_body_422.py` | `test_bill_issue_update_empty_body_422.md` | Empty payload body `{}` | Returns `422` validation error |
| `test_bill_issue_update_paid_409.py` | `test_bill_issue_update_paid_409.md` | Attempt to update already paid issue | Returns `409 BILL_ISSUE_ALREADY_PAID` |
| `test_bill_issue_update_period_conflict_409.py` | `test_bill_issue_update_period_conflict_409.md` | Target period occupied by another issue | Returns `409 BILL_ISSUE_PERIOD_CONFLICT` |
| `test_bill_issue_update_not_found_404.py` | `test_bill_issue_update_not_found_404.md` | Update non-existent issue ID | Returns `404 Not Found` |
| `test_bill_issue_update_other_user_404.py` | `test_bill_issue_update_other_user_404.md` | User B attempts to update User A's issue | Returns `404 Not Found` (ownership shield) |

---

### Bill Service Update Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_bill_service_update_full.py` | `test_bill_service_update_full.md` | Full update (5 fields) | Returns `200`; all 5 fields updated |
| `test_bill_service_update_partial.py` | `test_bill_service_update_partial.md` | Partial update (name, is_active) | Returns `200`; specified fields updated |
| `test_bill_service_update_empty_body_422.py` | `test_bill_service_update_empty_body_422.md` | Empty payload body `{}` | Returns `422` validation error |
| `test_bill_service_update_not_found_404.py` | `test_bill_service_update_not_found_404.md` | Update non-existent service ID | Returns `404 BILL_SERVICE_NOT_FOUND` |
| `test_bill_service_update_other_user_404.py` | `test_bill_service_update_other_user_404.md` | User B attempts to update User A's service | Returns `404 BILL_SERVICE_NOT_FOUND` (ownership shield) |

---

### Category Update Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_category_update_full.py` | `test_category_update_full.md` | Full update (name, description, is_income) | Returns `200`; all 3 fields updated |
| `test_category_update_partial.py` | `test_category_update_partial.md` | Partial update (name only) | Returns `200`; name updated |
| `test_category_update_empty_body_422.py` | `test_category_update_empty_body_422.md` | Empty payload body `{}` | Returns `422` validation error |
| `test_category_update_with_expenses_blocked_400.py` | `test_category_update_with_expenses_blocked_400.md` | Attempt to mutate `is_income` with expenses | Returns `400 CATEGORY_HAS_EXPENSES`; name updates remain allowed |
| `test_category_update_other_user_403.py` | `test_category_update_other_user_403.md` | User 2 attempts to update User 1's category | Returns `403 FORBIDDEN_OPERATION` |

---

### Expense Deletion Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_expense_delete_purchase_installments_ok.py` | `test_expense_delete_purchase_installments_ok.md` | Delete purchase expense with installments | Returns `200`; expense and all payment rows cascade deleted in DB |
| `test_expense_delete_subscription_ok.py` | `test_expense_delete_subscription_ok.md` | Delete subscription expense | Returns `200`; subscription record removed from DB |

---

### Projections Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_projections_end_to_end.py` | `test_projections_end_to_end.md` | E2E flow: card -> installment purchase -> projection query | Returns `200`; `total_expenses` correctly calculates monthly installment amount |

---

### Purchase Creation & Installment Split Scenarios

| Python Test File | Spec Document (`docs/integration_tests/`) | Scenario Description | Expected Result |
|---|---|---|---|
| `test_purchase_payments_exact_division.py` | `test_purchase_payments_exact_division.md` | Create purchase with evenly divisible amount | Returns `201`; DB contains 3 unconfirmed payments summing to total amount |
| `test_purchase_payments_non_divisible_redistribution.py` | `test_purchase_payments_non_divisible_redistribution.md` | Non-divisible amount, dynamic redistribution, status locking, 422 guard | Returns `201`; redistribution recalculates unconfirmed siblings; 422 raised when unconfirmed pool is exhausted |
