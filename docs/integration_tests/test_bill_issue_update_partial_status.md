---
test_id: "INT-API-BILL-ISSUE-UPDATE-PARTIAL-STATUS"
title: "Bill Issue Partial Status Update Scenario"
target_file: "tests/api/v1/test_bill_issue_update_partial_status.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "status"]
---

# Integration Test Specification: Bill Issue Partial Status Update (`test_bill_issue_update_partial_status.py`)

## 1. Description & Purpose
Verifies updating only the `status` field of a bill issue to `"cancelled"`.

---

## 2. Preconditions & Test Data
- Issue created (`amount="200.00"`). Payload: `{"status": "cancelled"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{id}` with `{"status": "cancelled"}`.
2. Assert status `200 OK` and verify status updated while other fields remain intact.
