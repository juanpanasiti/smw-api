---
test_id: "INT-API-BILL-SERVICE-UPDATE-PARTIAL"
title: "Bill Service Partial Update Scenario"
target_file: "tests/api/v1/test_bill_service_update_partial.py"
type: "backend"
status: "active"
tags: ["bills", "services", "patch", "partial"]
---

# Integration Test Specification: Bill Service Partial Update (`test_bill_service_update_partial.py`)

## 1. Description & Purpose
Verifies partial update of selected bill service fields (`name`, `is_active`).

---

## 2. Preconditions & Test Data
- Service created. Payload: `{"name": "Partial Name", "is_active": false}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/services/{id}`.
2. Assert status `200 OK` and verify specified fields change while unmentioned fields stay intact.
