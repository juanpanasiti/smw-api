---
test_id: "INT-API-BILL-SERVICE-UPDATE-NOT-FOUND-404"
title: "Bill Service Non-Existent ID 404 Scenario"
target_file: "tests/api/v1/test_bill_service_update_not_found_404.py"
type: "backend"
status: "active"
tags: ["bills", "services", "patch", "404"]
---

# Integration Test Specification: Bill Service Not Found (`test_bill_service_update_not_found_404.py`)

## 1. Description & Purpose
Verifies that attempting to update a non-existent bill service ID returns `404 Not Found` with error code `BILL_SERVICE_NOT_FOUND`.

---

## 2. Preconditions & Test Data
- Random non-existent UUID.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/services/{random_uuid}` with `{"name": "Ghost Service"}`.
2. Assert status `404 Not Found` and error code `BILL_SERVICE_NOT_FOUND`.
