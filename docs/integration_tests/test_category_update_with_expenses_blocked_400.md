---
test_id: "INT-API-CATEGORY-UPDATE-WITH-EXPENSES-BLOCKED-400"
title: "Category is_income Mutation Blocked with Expenses 400 Scenario"
target_file: "tests/api/v1/test_category_update_with_expenses_blocked_400.py"
type: "backend"
status: "active"
tags: ["categories", "patch", "expenses", "400", "is_income_guard"]
---

# Integration Test Specification: Category is_income Guard with Expenses (`test_category_update_with_expenses_blocked_400.py`)

## 1. Description & Purpose
Verifies that updating `is_income` on a category that already has linked expenses returns `400 Bad Request` (`CATEGORY_HAS_EXPENSES`), while updating non-`is_income` fields (such as `name`) succeeds.

---

## 2. Preconditions & Test Data
- Category created and linked to an expense purchase.
- Body 1: `{"is_income": true}`.
- Body 2: `{"name": "New Name"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/categories/{id}` with `{"is_income": true}`.
2. Assert status `400 Bad Request` and error code `CATEGORY_HAS_EXPENSES`.
3. Send `PATCH /api/v1/categories/{id}` with `{"name": "New Name"}`.
4. Assert status `200 OK`.
