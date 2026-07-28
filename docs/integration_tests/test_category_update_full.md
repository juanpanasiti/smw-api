---
test_id: "INT-API-CATEGORY-UPDATE-FULL"
title: "Category Full Update Scenario"
target_file: "tests/api/v1/test_category_update_full.py"
type: "backend"
status: "active"
tags: ["categories", "patch", "full_update"]
---

# Integration Test Specification: Category Full Update (`test_category_update_full.py`)

## 1. Description & Purpose
Verifies full update of category fields (`name`, `description`, `is_income`).

---

## 2. Preconditions & Test Data
- Category created. Payload: `{"name": "Updated Category", "description": "Updated description", "is_income": true}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/categories/{id}` with full payload.
2. Assert status `200 OK` and verify all 3 fields updated.
