---
test_id: "INT-API-EXPENSE-DELETE-PURCHASE-INSTALLMENTS-OK"
title: "Delete Purchase Expense With Installments Scenario"
target_file: "tests/api/v1/test_expense_delete_purchase_installments_ok.py"
type: "backend"
status: "active"
tags: ["expenses", "deletion", "purchase", "cascade"]
---

# Integration Test Specification: Delete Purchase Expense (`test_expense_delete_purchase_installments_ok.py`)

## 1. Description & Purpose
Verifies deleting a purchase expense with 3 installments, asserting cascade deletion of all child payment rows in DB.

---

## 2. Preconditions & Test Data
- Credit card and purchase with 3 installments created.

---

## 3. Step-by-Step Execution Sequence
1. Send `DELETE /api/v1/expenses/{id}`.
2. Assert status `200 OK`.
3. Verify in DB that Expense and all 3 Payment records are deleted.
