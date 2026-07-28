---
test_id: "INT-API-BILL-DELETE-SERVICE-WITH-ISSUES-NO-FORCE"
title: "Delete Service With Issues Without Force Flag Guard"
target_file: "tests/api/v1/test_bill_delete_service_with_issues_no_force.py"
type: "backend"
status: "active"
tags: ["bills", "services", "deletion", "409", "guard"]
---

# Integration Test Specification: Delete Service with Issues (No Force) (`test_bill_delete_service_with_issues_no_force.py`)

## 1. Description & Purpose
Verifies that attempting to delete a service with linked issues without specifying `?force=true` returns `409 Conflict` and leaves both the service and its issues intact.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies & Setup
- Category, Bill Service, and Bill Issue (`period="2027-02"`) created.

### 2.2 Input Request
- **HTTP Method:** `DELETE`
- **Path:** `/api/v1/bills/services/{service_id}` (no query param)
- **Headers:** `Authorization: Bearer <TOKEN>`, `Idempotency-Key: <UUID>`

---

## 3. Step-by-Step Execution Sequence
1. Create category, service, and issue.
2. Send `DELETE /api/v1/bills/services/{service_id}` without `force=true`.
3. Assert status is `409 Conflict` and error code is `BILL_SERVICE_HAS_ISSUES`.
4. Perform `GET /api/v1/bills/services` and `GET /api/v1/bills/issues?period=2027-02`.
5. Assert both service and issue still exist.

---

## 4. Expected Results & Assertions
- Status: `409 Conflict`.
- Error Code: `BILL_SERVICE_HAS_ISSUES`.
- Service and issue persist.
