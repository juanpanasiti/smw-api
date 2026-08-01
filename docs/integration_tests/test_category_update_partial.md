---
test_id: "INT-API-CATEGORY-UPDATE-PARTIAL"
title: "Category Partial Update Scenario"
target_file: "tests/api/v1/test_category_update_partial.py"
type: "backend"
status: "active"
tags: ["categories", "patch", "partial"]
---

# Integration Test Specification: Category Partial Update (`test_category_update_partial.py`)

## 1. Description & Purpose
Verifies partial update of `name` field on a category.

---

## 2. Preconditions & Test Data
- Category created. Payload: `{"name": "Partially Updated Category"}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/categories/{id}`.
2. Assert status `200 OK` and verify name updated while `is_income` remains unchanged.
