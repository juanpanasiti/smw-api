---
test_id: "INT-API-BILL-ISSUE-UPDATE-PERIOD-CONFLICT-409"
title: "Bill Issue Period Conflict 409 Scenario"
target_file: "tests/api/v1/test_bill_issue_update_period_conflict_409.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "409", "period_conflict"]
---

# Integration Test Specification: Bill Issue Period Conflict (`test_bill_issue_update_period_conflict_409.py`)

## 1. Description & Purpose
Verifies that attempting to update an issue's period to one already taken by another issue of the same service returns `409 Conflict` (`BILL_ISSUE_PERIOD_CONFLICT`).

---

## 2. Preconditions & Test Data
- Two issues created for periods `"2026-01"` and `"2026-02"`.

---

## 3. Step-by-Step Execution Sequence
1. Attempt `PATCH /api/v1/bills/issues/{id}` to move issue 1 to `"2026-02"`.
2. Assert status `409 Conflict` and error code `BILL_ISSUE_PERIOD_CONFLICT`.
