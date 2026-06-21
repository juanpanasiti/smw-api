# API Reference

> Complete endpoint reference for the Personal Finance API.
> All endpoints are prefixed with `/api/v1` and require a `Bearer` token in the `Authorization` header unless stated otherwise.

---

## Table of Contents

- [Global Conventions](#global-conventions)
  - [Base URL](#base-url)
  - [Authentication](#authentication)
  - [Idempotency](#idempotency)
  - [Standard Response Envelope](#standard-response-envelope)
  - [Error Response](#error-response)
- [Auth](#auth)
  - [POST /auth/register](#post-authregister)
  - [POST /auth/login](#post-authlogin)
  - [POST /auth/refresh](#post-authrefresh)
- [Categories](#categories)
  - [GET /categories/](#get-categories)
  - [POST /categories/](#post-categories)
  - [DELETE /categories/{category_id}](#delete-categoriescategory_id)
- [Accounts](#accounts)
  - [GET /accounts/](#get-accounts)
  - [POST /accounts/credit-cards](#post-accountscredit-cards)
  - [PATCH /accounts/credit-cards/{account_id}](#patch-accountscredit-cardsaccount_id)
  - [DELETE /accounts/{account_id}](#delete-accountsaccount_id)
- [Expenses & Payments](#expenses--payments)
  - [GET /expenses/](#get-expenses)
  - [POST /expenses/purchase](#post-expensespurchase)
  - [POST /expenses/subscription](#post-expensessubscription)
  - [PATCH /expenses/payments/{payment_id}](#patch-expensespaymentspayment_id)
- [Bills](#bills)
  - [GET /bills/services](#get-billsservices)
  - [POST /bills/services](#post-billsservices)
  - [GET /bills/issues](#get-billsissues)
  - [POST /bills/issues](#post-billsissues)
  - [POST /bills/issues/{issue_id}/pay](#post-billsissuesissue_idpay)
- [Projections](#projections)
  - [GET /projections/periods](#get-projectionperiods)
  - [GET /projections/periods/{period}](#get-projectionperiodperiod)
- [Health](#health)

---

## Global Conventions

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

All endpoints except `/auth/register` and `/auth/login` require a JWT Bearer token obtained from the login endpoint.

```http
Authorization: Bearer <access_token>
```

### Idempotency

All `POST`, `PATCH`, and `DELETE` mutating endpoints require an `Idempotency-Key` header containing a unique UUID v4. Duplicate requests with the same key within a **5-second window** return the cached response without re-executing the operation.

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

> Generate one on the fly with: `uuidgen` (Linux/macOS) or `[System.Guid]::NewGuid()` (PowerShell).

### Standard Response Envelope

All endpoints (except `/auth/login`) wrap their payload in the following envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

| Field     | Type            | Description                                        |
|-----------|-----------------|----------------------------------------------------|
| `success` | `boolean`       | `true` on success, `false` on business logic error |
| `data`    | `object\|null`  | The response payload                               |
| `error`   | `object\|null`  | Populated only when `success` is `false`           |

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "STRING_CONSTANT_ERROR_CODE",
    "message": "Human-readable explanation.",
    "details": {}
  }
}
```

| Field           | Type     | Description                                  |
|-----------------|----------|----------------------------------------------|
| `error.code`    | `string` | Machine-readable constant (e.g. `NOT_FOUND`) |
| `error.message` | `string` | Human-readable description                   |
| `error.details` | `object` | Additional context (field errors, etc.)      |

---

## Auth

### POST /auth/register

Creates a new user account along with their profile.

- **Auth required:** No
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "birthdate": "1990-01-15",
    "monthly_spending_limit": "3000.00"
  }
}
```

| Field                            | Type       | Constraints               |
|----------------------------------|------------|---------------------------|
| `email`                          | `string`   | Valid email format        |
| `password`                       | `string`   | Minimum 8 characters      |
| `profile.first_name`             | `string`   | Max 100 characters        |
| `profile.last_name`              | `string`   | Max 100 characters        |
| `profile.birthdate`              | `date`     | `YYYY-MM-DD`              |
| `profile.monthly_spending_limit` | `Decimal`  | ≥ 0.00, up to 12 digits, 2 decimal places |

#### Response `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "email": "user@example.com",
    "role": "user",
    "profile": {
      "id": "e5f6g7h8-...",
      "first_name": "John",
      "last_name": "Doe",
      "birthdate": "1990-01-15",
      "monthly_spending_limit": "3000.00"
    }
  },
  "error": null
}
```

---

### POST /auth/login

Authenticates a user and returns JWT access and refresh tokens.

- **Auth required:** No
- **Idempotency-Key required:** No
- **Content-Type:** `application/x-www-form-urlencoded`

#### Request Body (form-encoded)

| Field      | Type     | Description          |
|------------|----------|----------------------|
| `username` | `string` | The user's email     |
| `password` | `string` | The user's password  |

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPass123!"
```

#### Response `200 OK`

> ⚠️ This endpoint returns the token object **directly**, not wrapped in the standard envelope.

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### POST /auth/refresh

Renews an expired access token using a valid refresh token. This endpoint uses **Refresh Token Rotation**, returning both a new access token and a new refresh token.

- **Auth required:** No
- **Idempotency-Key required:** No
- **Content-Type:** `application/json`

#### Request Body

```json
{
  "refresh_token": "<jwt>"
}
```

| Field           | Type     | Description                               |
|-----------------|----------|-------------------------------------------|
| `refresh_token` | `string` | The refresh token obtained during login   |

#### Response `200 OK`

> ⚠️ This endpoint returns the token object **directly**, just like `/auth/login`.

```json
{
  "access_token": "<new_jwt>",
  "refresh_token": "<new_jwt>",
  "token_type": "bearer"
}
```

---

## Categories

Movement categories are used to classify expenses and bill services. They can be system-defined (shared, `user_id = null`) or user-created.

### GET /categories/

Returns all categories visible to the authenticated user (system categories + their own).

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "a1b2c3d4-...",
      "user_id": null,
      "name": "Groceries",
      "description": "Supermarket and food purchases",
      "is_income": false
    }
  ],
  "error": null
}
```

| Field         | Type            | Description                                  |
|---------------|-----------------|----------------------------------------------|
| `id`          | `UUID`          | Category identifier                          |
| `user_id`     | `UUID\|null`    | `null` for system-defined categories         |
| `name`        | `string`        | Category name                                |
| `description` | `string\|null`  | Optional description                         |
| `is_income`   | `boolean`       | `true` if this category represents income    |

---

### POST /categories/

Creates a new movement category for the authenticated user.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "name": "Streaming",
  "description": "Monthly streaming subscriptions",
  "is_income": false
}
```

| Field         | Type      | Constraints         |
|---------------|-----------|---------------------|
| `name`        | `string`  | Required, max 100 chars |
| `description` | `string`  | Optional, max 1000 chars |
| `is_income`   | `boolean` | Default: `false`    |

#### Response `201 Created`

Returns the created category object wrapped in the standard envelope.

---

### DELETE /categories/{category_id}

Deletes a user-defined category. System categories (`user_id = null`) cannot be deleted.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Path Parameters

| Parameter     | Type   | Description          |
|---------------|--------|----------------------|
| `category_id` | `UUID` | The category to delete |

#### Response `200 OK`

```json
{
  "success": true,
  "data": null,
  "error": null
}
```

#### Error Codes

| HTTP Status | `error.code`         | Description                                 |
|-------------|----------------------|---------------------------------------------|
| `404`       | `CATEGORY_NOT_FOUND` | Category does not exist                     |
| `403`       | `FORBIDDEN_OPERATION`| Attempted to delete a system-level category |

---

## Accounts

Accounts use a polymorphic model. Currently only **Credit Cards** are supported for creation. The list endpoint returns a discriminated union serialized by `account_type`.

### GET /accounts/

Returns all accounts owned by the authenticated user.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "a1b2c3d4-...",
      "owner_id": "u1u2u3u4-...",
      "alias": "Visa Gold",
      "is_enabled": true,
      "account_type": "credit_card",
      "closing_day": 15,
      "due_day": 5,
      "limit": "50000.00",
      "financing_limit": "10000.00",
      "main_credit_card_id": null
    }
  ],
  "error": null
}
```

The `account_type` discriminator field determines the shape of each item:

| `account_type` | Description                     |
|----------------|---------------------------------|
| `credit_card`  | Credit card with limit and days |
| `account`      | Standard bank account           |

---

### POST /accounts/credit-cards

Creates a new credit card account.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "alias": "Visa Gold",
  "is_enabled": true,
  "closing_day": 15,
  "due_day": 5,
  "limit": "50000.00",
  "financing_limit": "10000.00",
  "main_credit_card_id": null
}
```

| Field                  | Type           | Constraints                                        |
|------------------------|----------------|----------------------------------------------------|
| `alias`                | `string`       | Required, max 100 chars                            |
| `is_enabled`           | `boolean`      | Default: `true`                                    |
| `closing_day`          | `integer`      | Required, 1–31                                     |
| `due_day`              | `integer`      | Required, 1–31                                     |
| `limit`                | `Decimal`      | Required, > 0.00, up to 12 digits, 2 decimal places |
| `financing_limit`      | `Decimal`      | Required, ≥ 0.00, up to 12 digits, 2 decimal places |
| `main_credit_card_id`  | `UUID\|null`   | Optional — links this as an extension card         |

#### Response `201 Created`

Returns the created `CreditCardResponseSchema` wrapped in the standard envelope.

---

### PATCH /accounts/credit-cards/{account_id}

Partially updates a credit card. All fields are optional.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Path Parameters

| Parameter    | Type   | Description              |
|--------------|--------|--------------------------|
| `account_id` | `UUID` | The credit card to update |

#### Request Body

```json
{
  "alias": "Visa Platinum",
  "limit": "80000.00",
  "is_enabled": true
}
```

| Field             | Type         | Constraints                                         |
|-------------------|--------------|-----------------------------------------------------|
| `alias`           | `string`     | Optional, max 100 chars                             |
| `is_enabled`      | `boolean`    | Optional                                            |
| `closing_day`     | `integer`    | Optional, 1–31                                      |
| `due_day`         | `integer`    | Optional, 1–31                                      |
| `limit`           | `Decimal`    | Optional, > 0.00, up to 12 digits, 2 decimal places |
| `financing_limit` | `Decimal`    | Optional, ≥ 0.00, up to 12 digits, 2 decimal places |

#### Response `200 OK`

Returns the updated `CreditCardResponseSchema` wrapped in the standard envelope.

---

### DELETE /accounts/{account_id}

Deletes an account owned by the authenticated user.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Path Parameters

| Parameter    | Type   | Description           |
|--------------|--------|-----------------------|
| `account_id` | `UUID` | The account to delete |

#### Response `200 OK`

```json
{
  "success": true,
  "data": null,
  "error": null
}
```

---

## Expenses & Payments

Expenses use Single Table Inheritance. A **Purchase** is installment-based (generates N payments), while a **Subscription** is recurring (generates payments indefinitely). The list endpoint returns a discriminated union by `expense_type`.

### GET /expenses/

Returns all expenses for the authenticated user, with optional filters.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Query Parameters

| Parameter    | Type      | Description                                     |
|--------------|-----------|-------------------------------------------------|
| `account_id` | `UUID`    | Optional — filter by account                    |
| `is_active`  | `boolean` | Optional — filter by active/inactive state      |

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "e1e2e3e4-...",
      "account_id": "a1b2c3d4-...",
      "category_id": "c1c2c3c4-...",
      "title": "MacBook Pro",
      "account_name": "Visa Gold",
      "acquired_at": "2025-01-10",
      "amount": "2400.00",
      "first_payment_date": "2025-02-05",
      "is_active": true,
      "description": null,
      "version_id": 1,
      "expense_type": "purchase",
      "total_installments": 12
    }
  ],
  "error": null
}
```

The `expense_type` discriminator determines the shape of each item:

| `expense_type` | Extra field          | Description              |
|----------------|----------------------|--------------------------|
| `purchase`     | `total_installments` | Fixed installment count  |
| `subscription` | —                    | Indefinitely recurring   |
| `expense`      | —                    | Generic base type        |

---

### POST /expenses/purchase

Creates a new purchase expense and auto-generates its installment payments.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "account_id": "a1b2c3d4-...",
  "category_id": "c1c2c3c4-...",
  "title": "MacBook Pro",
  "account_name": "Visa Gold",
  "acquired_at": "2025-01-10",
  "amount": "2400.00",
  "first_payment_date": "2025-02-05",
  "description": "Work laptop",
  "total_installments": 12
}
```

| Field                | Type          | Constraints                                         |
|----------------------|---------------|-----------------------------------------------------|
| `account_id`         | `UUID`        | Required                                            |
| `category_id`        | `UUID\|null`  | Optional                                            |
| `title`              | `string`      | Required, max 255 chars                             |
| `account_name`       | `string`      | Required, max 255 chars (denormalized display name) |
| `acquired_at`        | `date`        | Required, `YYYY-MM-DD`                              |
| `amount`             | `Decimal`     | Required, > 0.00, up to 12 digits, 2 decimal places |
| `first_payment_date` | `date`        | Required, `YYYY-MM-DD`                              |
| `description`        | `string\|null`| Optional, max 1000 chars                            |
| `total_installments` | `integer`     | Required, ≥ 1                                       |

#### Response `201 Created`

Returns the created `PurchaseResponseSchema` wrapped in the standard envelope.

---

### POST /expenses/subscription

Creates a new subscription expense that generates recurring monthly payments.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

Same as [POST /expenses/purchase](#post-expensespurchase) **without** the `total_installments` field.

```json
{
  "account_id": "a1b2c3d4-...",
  "category_id": "c1c2c3c4-...",
  "title": "Netflix",
  "account_name": "Visa Gold",
  "acquired_at": "2025-01-01",
  "amount": "18.00",
  "first_payment_date": "2025-01-15",
  "description": null
}
```

#### Response `201 Created`

Returns the created `SubscriptionResponseSchema` wrapped in the standard envelope.

---

### PATCH /expenses/payments/{payment_id}

Updates the status of a specific payment. Uses **optimistic locking** — the `version_id` of the current payment record must be provided to prevent concurrent update conflicts.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Path Parameters

| Parameter    | Type   | Description             |
|--------------|--------|-------------------------|
| `payment_id` | `UUID` | The payment to update   |

#### Request Body

```json
{
  "status": "paid",
  "version_id": 1
}
```

| Field        | Type      | Description                                                    |
|--------------|-----------|----------------------------------------------------------------|
| `status`     | `string`  | New payment status (e.g. `paid`, `pending`)                    |
| `version_id` | `integer` | Current version of the record — required for optimistic locking |

#### Response `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "p1p2p3p4-...",
    "expense_id": "e1e2e3e4-...",
    "amount": "200.00",
    "no_installment": 3,
    "period_month": 4,
    "period_year": 2025,
    "status": "paid",
    "is_last_payment": false,
    "credit_card_code": null,
    "version_id": 2
  },
  "error": null
}
```

> **Optimistic locking:** If the record was modified by another request between your read and this update, a `409 Conflict` is returned. Retry by fetching the latest `version_id` and resubmitting.

---

## Bills

Bills follow a **master-detail** pattern. A **Bill Service** is the recurring service definition (e.g. "Electricity"). A **Bill Issue** is a specific monthly invoice for that service.

### GET /bills/services

Returns all bill services for the authenticated user.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "category_id": "c1c2c3c4-...",
      "name": "Electricity",
      "service_type": "utility",
      "expected_arrival_day": 10,
      "is_active": true,
      "id": "s1s2s3s4-...",
      "user_id": "u1u2u3u4-...",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "error": null
}
```

---

### POST /bills/services

Creates a new recurring bill service.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "category_id": "c1c2c3c4-...",
  "name": "Electricity",
  "service_type": "utility",
  "expected_arrival_day": 10,
  "is_active": true
}
```

| Field                  | Type      | Constraints                           |
|------------------------|-----------|---------------------------------------|
| `category_id`          | `UUID`    | Required                              |
| `name`                 | `string`  | Required, max 100 chars               |
| `service_type`         | `string`  | Required, max 50 chars (e.g. `utility`, `internet`) |
| `expected_arrival_day` | `integer` | Required, 1–31                        |
| `is_active`            | `boolean` | Default: `true`                       |

#### Response `201 Created`

Returns the created `BillServiceResponseSchema` wrapped in the standard envelope.

---

### GET /bills/issues

Returns all bill issues for a given period.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Query Parameters

| Parameter | Type     | Constraints              | Description          |
|-----------|----------|--------------------------|----------------------|
| `period`  | `string` | Required, format `YYYY-MM` | The billing period |

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "period": "2025-04",
      "amount": "8500.00",
      "due_date": "2025-04-20",
      "id": "i1i2i3i4-...",
      "bill_service_id": "s1s2s3s4-...",
      "status": "pending",
      "expense_id": null,
      "created_at": "2025-04-01T00:00:00Z",
      "updated_at": "2025-04-01T00:00:00Z",
      "bill_service": { ... }
    }
  ],
  "error": null
}
```

| `status` value | Description                               |
|----------------|-------------------------------------------|
| `pending`      | Invoice received, not yet paid            |
| `paid`         | Invoice has been paid                     |

---

### POST /bills/issues

Registers a new monthly invoice (issue) for an existing bill service.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Request Body

```json
{
  "bill_service_id": "s1s2s3s4-...",
  "period": "2025-04",
  "amount": "8500.00",
  "due_date": "2025-04-20"
}
```

| Field             | Type      | Constraints                                         |
|-------------------|-----------|-----------------------------------------------------|
| `bill_service_id` | `UUID`    | Required — must belong to the authenticated user    |
| `period`          | `string`  | Required, format `YYYY-MM`                          |
| `amount`          | `Decimal` | Required, > 0.00, up to 12 digits, 2 decimal places |
| `due_date`        | `date`    | Required, `YYYY-MM-DD`                              |

#### Response `201 Created`

Returns the created `BillIssueResponseSchema` wrapped in the standard envelope.

---

### POST /bills/issues/{issue_id}/pay

Marks a bill issue as paid by creating an associated expense linked to a specific account.

- **Auth required:** Yes
- **Idempotency-Key required:** Yes

#### Path Parameters

| Parameter  | Type   | Description           |
|------------|--------|-----------------------|
| `issue_id` | `UUID` | The bill issue to pay |

#### Request Body

```json
{
  "account_id": "a1b2c3d4-..."
}
```

| Field        | Type   | Description                                     |
|--------------|--------|-------------------------------------------------|
| `account_id` | `UUID` | The account to charge the payment against       |

#### Response `200 OK`

Returns the updated `BillIssueResponseSchema` with `status: "paid"` and the generated `expense_id`, wrapped in the standard envelope.

---

## Projections

Projections compute a forward-looking financial snapshot for one or more periods. Results are cached in Redis and invalidated on relevant mutations.

### GET /projections/periods

Returns financial projections for multiple consecutive periods starting from a given month.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Query Parameters

| Parameter      | Type      | Constraints                  | Default       | Description                    |
|----------------|-----------|------------------------------|---------------|--------------------------------|
| `start_period` | `string`  | Format `YYYY-MM`             | Current month | First period to project        |
| `limit`        | `integer` | 1–60                         | `12`          | Number of periods to return    |

#### Response `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "period": "2025-04",
      "total_income": "150000.00",
      "total_expenses": "85000.00",
      "pending_bills": "8500.00",
      "available_budget": "56500.00",
      "credit_card_usage": [
        {
          "account_id": "a1b2c3d4-...",
          "alias": "Visa Gold",
          "total_debt": "30000.00",
          "limit": "50000.00",
          "available_limit": "20000.00"
        }
      ],
      "payments": [ ... ]
    }
  ],
  "error": null
}
```

| Field                             | Type      | Description                                      |
|-----------------------------------|-----------|--------------------------------------------------|
| `period`                          | `string`  | Period identifier `YYYY-MM`                      |
| `total_income`                    | `Decimal` | Sum of income-category movements                 |
| `total_expenses`                  | `Decimal` | Sum of expense payments due in this period       |
| `pending_bills`                   | `Decimal` | Sum of unpaid bill issues due in this period     |
| `available_budget`                | `Decimal` | `total_income - total_expenses - pending_bills`  |
| `credit_card_usage`               | `array`   | Per-card debt and limit snapshot                 |
| `credit_card_usage[].total_debt`  | `Decimal` | Total outstanding debt on the card               |
| `credit_card_usage[].available_limit` | `Decimal` | `limit - total_debt`                         |
| `payments`                        | `array`   | Individual payments due in this period           |

---

### GET /projections/periods/{period}

Returns the financial projection for a single specific period.

- **Auth required:** Yes
- **Idempotency-Key required:** No

#### Path Parameters

| Parameter | Type     | Constraints      | Description          |
|-----------|----------|------------------|----------------------|
| `period`  | `string` | Format `YYYY-MM` | The period to project |

#### Response `200 OK`

Same shape as a single item from the [GET /projections/periods](#get-projectionperiods) array.

---

## Health

### GET /health

Liveness check — no authentication required.

```json
{ "status": "ok" }
```
