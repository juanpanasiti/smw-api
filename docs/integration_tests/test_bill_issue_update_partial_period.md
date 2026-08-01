---
test_id: "INT-API-BILL-ISSUE-UPDATE-PARTIAL-PERIOD"
title: "Bill Issue Partial Period Update Scenario"
target_file: "tests/api/v1/test_bill_issue_update_partial_period.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "period"]
---

# Integration Test Specification: Bill Issue Partial Period Update (`test_bill_issue_update_partial_period.py`)

## 1. Description & Purpose
Verifies moving a bill issue to a new period when no conflicting issue exists for that service.

---

## 2. Preconditions & Test Data
- Issue created (`period="2025-08"`). Payload: `{"period": "2025-09"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/bills/issues/{id}` with `{"period": "2025-09"}`.
2. Assert status `200 OK` and verify period updated.
