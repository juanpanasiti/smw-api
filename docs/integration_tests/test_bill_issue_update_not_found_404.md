---
test_id: "INT-API-BILL-ISSUE-UPDATE-NOT-FOUND-404"
title: "Bill Issue Non-Existent ID 404 Scenario"
target_file: "tests/api/v1/test_bill_issue_update_not_found_404.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "404"]
---

# Integration Test Specification: Bill Issue Not Found (`test_bill_issue_update_not_found_404.py`)

## 1. Description & Purpose
Verifies that attempting to update a non-existent bill issue ID returns `404 Not Found`.

---

## 2. Preconditions & Test Data
- Random non-existent UUID.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{random_uuid}` with `{"amount": "50.00"}`.
2. Assert status `404 Not Found`.
