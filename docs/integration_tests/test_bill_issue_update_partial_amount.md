---
test_id: "INT-API-BILL-ISSUE-UPDATE-PARTIAL-AMOUNT"
title: "Bill Issue Partial Amount Update Scenario"
target_file: "tests/api/v1/test_bill_issue_update_partial_amount.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "amount"]
---

# Integration Test Specification: Bill Issue Partial Amount Update (`test_bill_issue_update_partial_amount.py`)

## 1. Description & Purpose
Verifies partial update of amount field on a bill issue, ensuring unprovided fields retain original values.

---

## 2. Preconditions & Test Data
- Issue created (`amount="100.00"`, `due_date="2025-05-10"`).
- Payload: `{"amount": "999.50"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{id}` with `{"amount": "999.50"}`.
2. Assert status `200 OK`.
3. Verify amount updated to `"999.50"`, while period and due_date remain intact.
