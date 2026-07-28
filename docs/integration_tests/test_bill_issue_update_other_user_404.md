---
test_id: "INT-API-BILL-ISSUE-UPDATE-OTHER-USER-404"
title: "Bill Issue Cross-User Update Ownership Shield 404 Scenario"
target_file: "tests/api/v1/test_bill_issue_update_other_user_404.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "security", "404"]
---

# Integration Test Specification: Bill Issue Cross-User Update (`test_bill_issue_update_other_user_404.py`)

## 1. Description & Purpose
Verifies that User B attempting to update an issue owned by User A receives `404 Not Found` to shield resource existence details.

---

## 2. Preconditions & Test Data
- Issue created by User A.
- Authenticated headers for User B.

---

## 3. Step-by-Step Execution Sequence
1. User A creates issue. User B registers and authenticates.
2. User B sends `PATCH /api/v1/bills/issues/{user_a_issue_id}` with `{"amount": "1.00"}`.
3. Assert status `404 Not Found`.
