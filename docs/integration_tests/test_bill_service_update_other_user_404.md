---
test_id: "INT-API-BILL-SERVICE-UPDATE-OTHER-USER-404"
title: "Bill Service Cross-User Ownership Shield 404 Scenario"
target_file: "tests/api/v1/test_bill_service_update_other_user_404.py"
type: "backend"
status: "active"
tags: ["bills", "services", "patch", "security", "404"]
---

# Integration Test Specification: Bill Service Cross-User Update (`test_bill_service_update_other_user_404.py`)

## 1. Description & Purpose
Verifies that User B attempting to update User A's service ID receives `404 Not Found` (`BILL_SERVICE_NOT_FOUND`) to shield resource existence details.

---

## 2. Preconditions & Test Data
- Service created by User A.
- Authenticated headers for User B.

---

## 3. Step-by-Step Execution Sequence
1. User A creates service. User B authenticates.
2. User B sends `PATCH /api/v1/bills/services/{user_a_service_id}` with `{"name": "Hijacked"}`.
3. Assert status `404 Not Found` and error code `BILL_SERVICE_NOT_FOUND`.
