---
test_id: "INT-API-CATEGORY-UPDATE-OTHER-USER-403"
title: "Category Cross-User Update Block 403 Scenario"
target_file: "tests/api/v1/test_category_update_other_user_403.py"
type: "backend"
status: "active"
tags: ["categories", "patch", "security", "403"]
---

# Integration Test Specification: Category Cross-User Update Block (`test_category_update_other_user_403.py`)

## 1. Description & Purpose
Verifies that User 2 attempting to update User 1's custom category returns `403 Forbidden` (`FORBIDDEN_OPERATION`).

---

## 2. Preconditions & Test Data
- Category created by User 1.
- Authenticated headers for User 2.

---

## 3. Step-by-Step Execution Sequence
1. User 1 creates category. User 2 authenticates.
2. User 2 sends `PATCH /api/v1/categories/{user_1_category_id}` with `{"name": "Hacked"}`.
3. Assert status `403 Forbidden` and error code `FORBIDDEN_OPERATION`.
