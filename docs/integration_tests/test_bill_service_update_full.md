---
test_id: "INT-API-BILL-SERVICE-UPDATE-FULL"
title: "Bill Service Full Update Scenario"
target_file: "tests/api/v1/test_bill_service_update_full.py"
type: "backend"
status: "active"
tags: ["bills", "services", "patch", "full_update"]
---

# Integration Test Specification: Bill Service Full Update (`test_bill_service_update_full.py`)

## 1. Description & Purpose
Verifies full update of all 5 updatable bill service fields (`category_id`, `name`, `service_type`, `expected_arrival_day`, `is_active`).

---

## 2. Preconditions & Test Data
- Created service and a target category UUID.
- Payload: `{"category_id": "<NEW_UUID>", "name": "Electricity Updated", "service_type": "electric", "expected_arrival_day": 20, "is_active": false}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/services/{id}` with full payload.
2. Assert status `200 OK` and verify all 5 fields updated.
