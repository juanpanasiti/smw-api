---
test_id: "INT-API-BILL-ISSUE-UPDATE-EMPTY-BODY-422"
title: "Bill Issue Empty Body 422 Validation Scenario"
target_file: "tests/api/v1/test_bill_issue_update_empty_body_422.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "validation", "422"]
---

# Integration Test Specification: Bill Issue Empty Body (`test_bill_issue_update_empty_body_422.py`)

## 1. Description & Purpose
Verifies that passing an empty `{}` JSON payload returns `422 Unprocessable Entity`.

---

## 2. Preconditions & Test Data
- Issue created. Payload: `{}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{id}` with `{}`.
2. Assert status `422 Unprocessable Entity` containing `"At least one field must be provided for update"`.
