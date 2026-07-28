---
test_id: "INT-API-BILL-ISSUE-UPDATE-FULL"
title: "Bill Issue Full Field Update Scenario"
target_file: "tests/api/v1/test_bill_issue_update_full.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "patch", "full_update"]
---

# Integration Test Specification: Bill Issue Full Update (`test_bill_issue_update_full.py`)

## 1. Description & Purpose
Verifies full update of all four updatable bill issue fields (`amount`, `due_date`, `period`, `status`) in a single `PATCH` request.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies
- Category, Service, and Issue (`period="2025-03"`) created.

### 2.2 Input Payload (`PATCH /api/v1/bills/issues/{id}`)
```json
{
  "amount": "299.99",
  "due_date": "2025-03-20",
  "period": "2025-04",
  "status": "cancelled"
}
```

---

## 3. Step-by-Step Execution Sequence
1. Create category, service, and issue.
2. Send `PATCH /api/v1/bills/issues/{id}` with full update payload.
3. Assert HTTP status `200 OK`.
4. Assert all 4 fields are updated in returned data.

---

## 4. Expected Results & Assertions
- Status: `200 OK`.
- `amount == "299.99"`, `due_date == "2025-03-20"`, `period == "2025-04"`, `status == "cancelled"`.
