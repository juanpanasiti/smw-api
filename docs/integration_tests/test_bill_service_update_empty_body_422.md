---
test_id: "INT-API-BILL-SERVICE-UPDATE-EMPTY-BODY-422"
title: "Bill Service Empty Body 422 Validation Scenario"
target_file: "tests/api/v1/test_bill_service_update_empty_body_422.py"
type: "backend"
status: "active"
tags: ["bills", "services", "patch", "validation", "422"]
---

# Integration Test Specification: Bill Service Empty Body (`test_bill_service_update_empty_body_422.py`)

## 1. Description & Purpose
Verifies that passing an empty `{}` JSON body to bill service update returns `422 Unprocessable Entity`.

---

## 2. Preconditions & Test Data
- Service created. Payload: `{}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/services/{id}` with `{}`.
2. Assert status `422 Unprocessable Entity` containing `"At least one field must be provided for update"`.
