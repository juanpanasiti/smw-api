---
test_id: "INT-API-BILL-DELETE-ISSUE-OK"
title: "Delete Existing Bill Issue Scenario"
target_file: "tests/api/v1/test_bill_delete_issue_ok.py"
type: "backend"
status: "active"
tags: ["bills", "issues", "deletion", "204"]
---

# Integration Test Specification: Delete Bill Issue (`test_bill_delete_issue_ok.py`)

## 1. Description & Purpose
Verifies successful deletion of an existing bill issue. After a `DELETE` request, the issue must be completely removed and no longer returned in period query lists.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies & Setup
- Created Category via `create_category`.
- Created Bill Service via `create_bill_service`.
- Created Bill Issue for period `"2027-01"` via `create_bill_issue`.

### 2.2 Input Request
- **HTTP Method:** `DELETE`
- **Path:** `/api/v1/bills/issues/{issue_id}`
- **Headers:** `Authorization: Bearer <TOKEN>`, `Idempotency-Key: <UUID>`

---

## 3. Step-by-Step Execution Sequence
1. Create a category, bill service, and bill issue for period `"2027-01"`.
2. Send `DELETE /api/v1/bills/issues/{issue_id}`.
3. Assert HTTP response status is `204 No Content`.
4. Perform `GET /api/v1/bills/issues?period=2027-01`.
5. Assert `issue_id` is absent from the returned list.

---

## 4. Expected Results & Assertions
- HTTP Status Code: `204 No Content`.
- `issue_id` not found in subsequent list queries for period `"2027-01"`.

---

## 5. Edge Cases & Error Handling
- Deleting an issue that does not exist returns HTTP `404 Not Found`.
