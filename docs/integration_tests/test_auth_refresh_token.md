---
test_id: "INT-API-AUTH-REFRESH-TOKEN"
title: "Token Refresh & Invalid Token Rejection Scenario"
target_file: "tests/api/v1/test_auth_refresh_token.py"
type: "backend"
status: "active"
tags: ["auth", "refresh", "jwt", "401"]
---

# Integration Test Specification: Token Refresh (`test_auth_refresh_token.py`)

## 1. Description & Purpose
Verifies token refresh functionality (`POST /api/v1/auth/refresh`) using valid refresh tokens and ensures invalid tokens are rejected with `401 Unauthorized` (`INVALID_REFRESH_TOKEN`).

---

## 2. Preconditions & Test Data

### 2.1 Dependencies
- User registered and logged in to acquire a initial `refresh_token`.

### 2.2 Input Payloads (`POST /api/v1/auth/refresh`)
- **Valid Body:** `{"refresh_token": "<OLD_REFRESH_TOKEN>"}`
- **Invalid Body:** `{"refresh_token": "invalid_token_string"}`

---

## 3. Step-by-Step Execution Sequence
1. Register user and log in to obtain `refresh_token`.
2. Send `POST /api/v1/auth/refresh` with valid token payload.
3. Assert status is `200 OK` and returns new token pair.
4. Send `POST /api/v1/auth/refresh` with invalid token payload.
5. Assert status is `401 Unauthorized` with code `INVALID_REFRESH_TOKEN`.

---

## 4. Expected Results & Assertions
- Valid refresh: `200 OK`, new tokens returned.
- Invalid refresh: `401 Unauthorized`, error code `INVALID_REFRESH_TOKEN`.
