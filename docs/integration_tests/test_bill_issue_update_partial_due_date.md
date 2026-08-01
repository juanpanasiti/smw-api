---
test_id: "INT-API-BILL-ISSUE-UPDATE-PARTIAL-DUE-DATE"
title: "Bill Issue Partial Due Date Update Scenario"
target_file: "tests/api/v1/test_bill_issue_update_partial_due_date.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "due_date"]
---

# Integration Test Specification: Bill Issue Partial Due Date Update (`test_bill_issue_update_partial_due_date.py`)

## 1. Description & Purpose
Verifies updating only the `due_date` field of a bill issue.

---

## 2. Preconditions & Test Data
- Issue created (`due_date="2025-07-05"`). Payload: `{"due_date": "2025-07-25"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{id}` with `{"due_date": "2025-07-25"}`.
2. Assert status `200 OK` and verify due date updated.
