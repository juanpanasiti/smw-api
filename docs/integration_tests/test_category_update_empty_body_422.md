---
test_id: "INT-API-CATEGORY-UPDATE-EMPTY-BODY-422"
title: "Category Empty Body 422 Validation Scenario"
target_file: "tests/api/v1/test_category_update_empty_body_422.py"
type: "backend"
status: "active"
tags: ["categories", "patch", "validation", "422"]
---

# Integration Test Specification: Category Empty Body (`test_category_update_empty_body_422.py`)

## 1. Description & Purpose
Verifies that passing an empty `{}` JSON body to category update returns `422 Unprocessable Entity`.

---

## 2. Preconditions & Test Data
- Category created. Payload: `{}`.

---

## 3. Step-by-Step Execution Sequence
1. Send `PATCH /api/v1/categories/{id}` with `{}`.
2. Assert status `422 Unprocessable Entity` containing `"At least one field must be provided for update"`.
