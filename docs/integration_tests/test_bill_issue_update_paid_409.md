---
test_id: "INT-API-BILL-ISSUE-UPDATE-PAID-409"
title: "Bill Issue Update Paid Lock Guard Scenario"
target_file: "tests/api/v1/test_bill_issue_update_paid_409.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "409", "paid_guard"]
---

# Integration Test Specification: Bill Issue Paid Update Guard (`test_bill_issue_update_paid_409.py`)

## 1. Description & Purpose
Verifies that attempting to update an issue in `"paid"` status returns `409 Conflict` with error code `BILL_ISSUE_ALREADY_PAID`.

---

## 2. Preconditions & Test Data
- Issue set to `"paid"` status.

---

## 3. Step-by-Step Execution Sequence
1. Update issue status to `"paid"`.
2. Attempt `PATCH /api/v1/bills/issues/{id}` with `{"amount": "999.00"}`.
3. Assert status `409 Conflict` and error code `BILL_ISSUE_ALREADY_PAID`.
