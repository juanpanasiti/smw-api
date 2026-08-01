---
test_id: "INT-API-BILL-DELETE-SERVICE-WITH-ISSUES-FORCE-OK"
title: "Force Delete Service With Issues Cascade Scenario"
target_file: "tests/api/v1/test_bill_delete_service_with_issues_force_ok.py"
type: "backend"
status: "active"
tags: ["bills", "services", "deletion", "force", "cascade", "204"]
---

# Integration Test Specification: Force Delete Service with Issues (`test_bill_delete_service_with_issues_force_ok.py`)

## 1. Description & Purpose
Verifies that passing `?force=true` forces deletion of a bill service and cascades to remove all associated bill issues.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies & Setup
- Category, Service, and two Issues (`2027-03` and `2027-04`) created.

### 2.2 Input Request
- **HTTP Method:** `DELETE`
- **Path:** `/api/v1/bills/services/{service_id}?force=true`
- **Headers:** `Authorization: Bearer <TOKEN>`, `Idempotency-Key: <UUID>`

---

## 3. Step-by-Step Execution Sequence
1. Create category, service, and two issues.
2. Send `DELETE /api/v1/bills/services/{service_id}?force=true`.
3. Assert status is `204 No Content`.
4. Verify service and both issues are removed in GET queries.

---

## 4. Expected Results & Assertions
- Status: `204 No Content`.
- Service and all child issues deleted.
