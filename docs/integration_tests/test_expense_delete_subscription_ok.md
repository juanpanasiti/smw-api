---
test_id: "INT-API-EXPENSE-DELETE-SUBSCRIPTION-OK"
title: "Delete Subscription Expense Scenario"
target_file: "tests/api/v1/test_expense_delete_subscription_ok.py"
type: "backend"
status: "active"
tags: ["expenses", "deletion", "subscription"]
---

# Integration Test Specification: Delete Subscription Expense (`test_expense_delete_subscription_ok.py`)

## 1. Description & Purpose
Verifies deleting a subscription expense record cleanly from the database.

---

## 2. Preconditions & Test Data
- Credit card and subscription expense created.

---

## 3. Step-by-Step Execution Sequence
1. Send `DELETE /api/v1/expenses/{id}`.
2. Assert status `200 OK`.
3. Verify in DB that Subscription Expense record is deleted.
