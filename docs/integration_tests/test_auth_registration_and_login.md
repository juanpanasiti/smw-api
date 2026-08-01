---
test_id: "INT-API-AUTH-REGISTRATION-AND-LOGIN"
title: "User Registration & Login Flow Scenario"
target_file: "tests/api/v1/test_auth_registration_and_login.py"
type: "backend"
status: "active"
tags: ["auth", "register", "login", "jwt"]
---

# Integration Test Specification: User Registration & Login (`test_auth_registration_and_login.py`)

## 1. Description & Purpose
Validates user registration via `POST /api/v1/auth/register` and subsequent authentication via `POST /api/v1/auth/login` to obtain access and refresh tokens.

---

## 2. Preconditions & Test Data

### 2.1 Registration Payload (`POST /api/v1/auth/register`)
- **Headers:** `Idempotency-Key: <UUID>`
- **Body:**
```json
{
  "email": "integration_<UUID>@test.com",
  "password": "Password123!",
  "profile": {
    "first_name": "Integration",
    "last_name": "Test",
    "birthdate": "1990-01-01",
    "monthly_spending_limit": "5000.00"
  }
}
```

### 2.2 Login Credentials (`POST /api/v1/auth/login`)
- **Headers:** `Content-Type: application/x-www-form-urlencoded`
- **Body:** `username=integration_<UUID>@test.com&password=Password123!`

---

## 3. Step-by-Step Execution Sequence
1. Send `POST /api/v1/auth/register` with registration payload.
2. Assert status is `201 Created` and response data email matches.
3. Send `POST /api/v1/auth/login` with form-encoded credentials.
4. Assert status is `200 OK` and returned JSON contains `access_token` and `refresh_token`.

---

## 4. Expected Results & Assertions
- Registration: `201 Created`, user profile initialized.
- Login: `200 OK`, JWT token pair generated.
