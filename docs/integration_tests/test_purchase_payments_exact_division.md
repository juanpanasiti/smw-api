---
test_id: "INT-API-PURCHASE-PAYMENTS-EXACT-DIVISION"
title: "Purchase Installments Exact Division Scenario"
target_file: "tests/api/v1/test_purchase_payments_exact_division.py"
type: "backend"
status: "active"
tags: ["expenses", "purchase", "installments", "exact_split"]
---

# Integration Test Specification: Purchase Exact Division (`test_purchase_payments_exact_division.py`)

## 1. Description & Purpose
Verifies creating a purchase with an evenly divisible amount (`1200.00 / 3 = 400.00`), asserting DB contains 3 unconfirmed payments summing exactly to `1200.00`.

---

## 2. Preconditions & Test Data
- Card created. Purchase payload: `amount="1200.00"`, `total_installments=3`.

---

## 3. Step-by-Step Execution Sequence
1. Send `POST /api/v1/expenses/purchase`.
2. Assert status `201 Created`.
3. Query DB: assert 3 Payment rows created, `sum(amount) == Decimal("1200.00")`, and status is `unconfirmed`.
