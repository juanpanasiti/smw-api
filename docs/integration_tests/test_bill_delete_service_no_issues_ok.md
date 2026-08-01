---
test_id: "INT-API-BILL-DELETE-SERVICE-NO-ISSUES-OK"
title: "Delete Service With No Issues Scenario"
target_file: "tests/api/v1/test_bill_delete_service_no_issues_ok.py"
type: "backend"
status: "active"
tags: ["bills", "services", "deletion", "204"]
---

# Integration Test Specification: Delete Service with No Issues (`test_bill_delete_service_no_issues_ok.py`)

## 1. Description & Purpose
Verifies successful deletion of a bill service that has no linked bill issues.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies & Setup
- Category created via `create_category`.
- Bill Service created via `create_bill_service` (no issues linked).

### 2.2 Input Request
- **HTTP Method:** `DELETE`
- **Path:** `/api/v1/bills/services/{service_id}`
- **Headers:** `Authorization: Bearer <TOKEN>`, `Idempotency-Key: <UUID>`

---

## 3. Step-by-Step Execution Sequence
1. Create category and bill service.
2. Send `DELETE /api/v1/bills/services/{service_id}`.
3. Assert status is `204 No Content`.
4. Perform `GET /api/v1/bills/services`.
5. Assert `service_id` is absent from returned list.

---

## 4. Expected Results & Assertions
- HTTP Status Code: `204 No Content`.
- Service removed from list response.
