---
test_id: "INT-API-PURCHASE-PAYMENTS-NON-DIVISIBLE-REDISTRIBUTION"
title: "Non-Divisible Purchase Installments & Dynamic Redistribution Scenario"
target_file: "tests/api/v1/test_purchase_payments_non_divisible_redistribution.py"
type: "backend"
status: "active"
tags: ["expenses", "purchase", "installments", "redistribution", "rounding"]
---

# Integration Test Specification: Non-Divisible Purchase Redistribution (`test_purchase_payments_non_divisible_redistribution.py`)

## 1. Description & Purpose
Verifies rounding algorithm for non-divisible purchase amounts (`100.00 / 3`), dynamic redistribution across unconfirmed siblings when editing installment amounts, status locking (`confirmed` / `paid`), and 422 error guard when unconfirmed siblings are exhausted.

---

## 2. Preconditions & Test Data
- Card created, purchase of `100.00` split into 3 installments created.

---

## 3. Step-by-Step Execution Sequence
1. Verify initial split `[33.33, 33.34, 33.33]` sums to `100.00`.
2. PATCH installment #1 to `33.35`: assert remaining unconfirmed redistribute to `[33.32, 33.33]`.
3. Confirm installment #1, PATCH installment #2 to `33.33`: assert installment #1 stays locked (`33.35`) and installment #3 absorbs remainder (`33.32`).
4. Set installments #1 and #2 to `"paid"`. Attempt to change installment #3 to `"10.00"`.
5. Assert status `422 Unprocessable Entity` with error code `PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL`.
