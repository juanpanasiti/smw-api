---
test_id: "INT-API-BILL-DELETE-SERVICE-FORCE-FAIL-ROLLBACK"
title: "Force Delete Service Failure Transactional Rollback Scenario"
target_file: "tests/api/v1/test_bill_delete_service_force_fail_rollback.py"
type: "backend"
status: "active"
tags: ["bills", "services", "deletion", "rollback", "transaction"]
---

# Integration Test Specification: Force Delete Service Failure Rollback (`test_bill_delete_service_force_fail_rollback.py`)

## 1. Description & Purpose
Verifies atomicity of the force-delete operation: if a database failure occurs mid-delete, the transaction aborts and leaves both the service and its issues intact in the DB.

---

## 2. Preconditions & Test Data

### 2.1 Dependencies & Setup
- Category, Service, and Issue (`2027-05`) created.
- `BillRepository.delete_service` patched to raise `RuntimeError`.

---

## 3. Step-by-Step Execution Sequence
1. Create category, service, and issue.
2. Patch repository to raise `RuntimeError`.
3. Send `DELETE /api/v1/bills/services/{service_id}?force=true`.
4. Capture exception with `pytest.raises`.
5. Query database endpoints and assert service and issue still exist.

---

## 4. Expected Results & Assertions
- Exception caught.
- Uncommitted transaction leaves service and issue intact.
