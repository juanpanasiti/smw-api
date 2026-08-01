---
test_id: "INT-API-PROJECTIONS-END-TO-END"
title: "Monthly Projections End-to-End Flow Scenario"
target_file: "tests/api/v1/test_projections_end_to_end.py"
type: "backend"
status: "active"
tags: ["projections", "periods", "e2e"]
---

# Integration Test Specification: Projections E2E (`test_projections_end_to_end.py`)

## 1. Description & Purpose
Verifies the end-to-end projection calculation flow (`GET /api/v1/projections/periods/{period}`) for a credit card purchase split into 3 installments (`1200.00 / 3 = 400.00`).

---

## 2. Preconditions & Test Data
- Card created, purchase of `1200.00` split into 3 installments starting next month.

---

## 3. Step-by-Step Execution Sequence
1. Create credit card and purchase expense.
2. Query `GET /api/v1/projections/periods/{YYYY-MM}` for the first installment period.
3. Assert status `200 OK`, `total_expenses == "400.00"`, and `payments[0]["amount"] == "400.00"`.
