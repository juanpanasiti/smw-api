# Backend API Architecture - Credit & Finance Management System

This document outlines the complete technical design, software patterns, data schemas, and deployment workflows for the production-ready Personal Finance and Projection API.

---

## 1. System Overview & Core Stack
The API is engineered for maximum horizontal scalability, strict financial data consistency, and state-of-the-art observability, serving both web (Next.js) and mobile (Expo) clients.

* **Language & Runtime:** Python 3.11+
* **Web Framework:** FastAPI (Asynchronous Event-Loop first approach)
* **Database ORM & Migrations:** SQLAlchemy (Async Engine) + Alembic
* **Primary Database:** PostgreSQL (Relational persistence)
* **Cache & Idempotency Layer:** Redis (In-memory structured key-value store)
* **Package Manager:** `uv` (Fast, Rust-backed dependency tracking)

---

## 2. Layered Software Architecture
The application strictly enforces a decoupling pattern across five layers. Inside domain boundaries, paths follow an isolated directional flow:

```text
[HTTP Request] ──> Routes (Functions) ──> Controller (Class) ──> Service (Class) ──> Repository (Class) ──> Models (SQLAlchemy)
```

1.  **Routes (Functions):** Pure stateless entrypoints. Extract and validate JWT claims, parse query parameters, and immediately delegate to the domain `Controller` instance resolved via FastAPI `Depends`.
    * All HTTP routes are versioned from day zero under the mandatory prefix `/api/v1`.
2.  **Controllers (Classes):** Orchestrate HTTP responses. They convert structural input payloads, call services, map domain execution outputs, and enforce standardized HTTP status codes (e.g., `201 Created` for resource creations).
3.  **Services (Classes):** The exclusive home of business logic. Calculates mathematical installment schedules for `Purchases`, handles dynamic flight simulation of `Subscriptions`, and processes dynamic service bill arrival windows.
4.  **Repositories (Classes):** Data abstraction layer. No raw queries or business constraints live here. They interact purely with SQLAlchemy `AsyncSession` to execute transactional mutations.
5.  **Models (SQLAlchemy):** Database entity schemas. Contains constraints, table mappings, and inheritance parameters.

---

## 3. Database Schema Design (PostgreSQL)

All currency operations strictly employ the `NUMERIC(12, 2)` type to prevent binary floating-point rounding errors. Temporary data structures (Periods) use an immutable `VARCHAR(7)` string mapping with format `YYYY-MM`.

### 3.1 Framework Core Entities

#### Table: `users`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `email` | `VARCHAR(255)` | `NOT NULL`, `UNIQUE`, `INDEX` |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` |
| `role` | `VARCHAR(50)` | `NOT NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

#### Table: `profiles`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `user_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` |
| `first_name` | `VARCHAR(100)` | `NOT NULL` |
| `last_name` | `VARCHAR(100)` | `NOT NULL` |
| `birthdate` | `DATE` | `NOT NULL` |
| `monthly_spending_limit`| `NUMERIC(12, 2)`| `NOT NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

#### Table: `movement_categories`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `user_id` | `UUID` | `NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` *(Null means global)* |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `description` | `VARCHAR(1000)`| `NULL` |
| `is_income` | `BOOLEAN` | `NOT NULL`, Default: `FALSE` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

### 3.2 Accounts Polymorphic Model (Joined Table Inheritance)

#### Table: `accounts`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `owner_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` |
| `alias` | `VARCHAR(100)` | `NOT NULL` |
| `is_enabled` | `BOOLEAN` | `NOT NULL`, Default: `TRUE` |
| `account_type` | `VARCHAR(50)` | `NOT NULL` *(Discriminator: 'credit_card', 'debit', etc.)* |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

#### Table: `credit_cards`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `FOREIGN KEY -> accounts(id) ON DELETE CASCADE` |
| `main_credit_card_id` | `UUID` | `NULL`, `FOREIGN KEY -> credit_cards(id)` *(For card extensions)* |
| `closing_day` | `SMALLINT` | `NOT NULL`, `CHECK (closing_day BETWEEN 1 AND 31)` |
| `due_day` | `SMALLINT` | `NOT NULL`, `CHECK (due_day BETWEEN 1 AND 31)` |
| `limit` | `NUMERIC(12, 2)`| `NOT NULL` |
| `financing_limit` | `NUMERIC(12, 2)`| `NOT NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

### 3.3 Expenses & Payments Model (Single Table Inheritance & Versioning)

#### Table: `expenses`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `account_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> accounts(id) ON DELETE CASCADE` |
| `category_id` | `UUID` | `NULL`, `FOREIGN KEY -> movement_categories(id) ON DELETE SET NULL` |
| `title` | `VARCHAR(255)` | `NOT NULL` |
| `account_name` | `VARCHAR(255)` | `NOT NULL` *(Bank statement matching label)* |
| `acquired_at` | `DATE` | `NOT NULL` |
| `amount` | `NUMERIC(12, 2)`| `NOT NULL`, `CHECK (amount > 0)` |
| `expense_type` | `VARCHAR(50)` | `NOT NULL` *(Discriminator: 'purchase', 'subscription')* |
| `total_installments` | `SMALLINT` | `NULL` *(Mandatory for 'purchase')* |
| `first_payment_date` | `DATE` | `NOT NULL` |
| `is_active` | `BOOLEAN` | `NOT NULL`, Default: `TRUE` |
| `description` | `VARCHAR(1000)`| `NULL` |
| `version_id` | `INTEGER` | `NOT NULL`, Default: `1` *(Optimistic Locking Field)* |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

#### Table: `payments`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `expense_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> expenses(id) ON DELETE CASCADE` |
| `amount` | `NUMERIC(12, 2)`| `NOT NULL`, `CHECK (amount > 0)` |
| `no_installment` | `SMALLINT` | `NOT NULL` |
| `period_month` | `SMALLINT` | `NOT NULL`, `CHECK (period_month BETWEEN 1 AND 12)` |
| `period_year` | `SMALLINT` | `NOT NULL` |
| `status` | `VARCHAR(50)` | `NOT NULL` *(Values: 'unconfirmed', 'confirmed', 'paid', 'canceled')* |
| `is_last_payment` | `BOOLEAN` | `NOT NULL`, Default: `FALSE` |
| `credit_card_code` | `VARCHAR(100)` | `NULL` |
| `version_id` | `INTEGER` | `NOT NULL`, Default: `1` *(Optimistic Locking Field)* |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

* **Database Constraints:** `UNIQUE (expense_id, period_year, period_month)` ensures no duplicate physical payment exists for the same expense in the same month.

### 3.4 Bills & Services Master-Detail Module

#### Table: `bill_services`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `user_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` |
| `category_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> movement_categories(id)` |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `service_type` | `VARCHAR(50)` | `NOT NULL` *(e.g., 'internet', 'electricity')* |
| `expected_arrival_day`| `SMALLINT` | `NOT NULL`, `CHECK (expected_arrival_day BETWEEN 1 AND 31)` |
| `is_active` | `BOOLEAN` | `NOT NULL`, Default: `TRUE` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

#### Table: `bill_issues`
| Column | Type | Constraints / Modifiers |
| :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` |
| `bill_service_id` | `UUID` | `NOT NULL`, `FOREIGN KEY -> bill_services(id) ON DELETE CASCADE` |
| `period` | `VARCHAR(7)` | `NOT NULL`, Regex Check Validation: `^[0-9]{4}-(0[1-9]\|1[0-2])$` |
| `amount` | `NUMERIC(12, 2)`| `NOT NULL` |
| `due_date` | `DATE` | `NOT NULL` |
| `status` | `VARCHAR(50)` | `NOT NULL`, Default: `'unpaid'` *(Values: 'unpaid', 'paid', 'overdue')* |
| `expense_id` | `UUID` | `NULL`, `FOREIGN KEY -> expenses(id) ON DELETE SET NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, Default: `NOW()` |

* **Database Constraints:** `UNIQUE (bill_service_id, period)` ensures only one bill issue is processed per monthly billing period.

---

## 4. Concurrency & State Validation Strategy
To guarantee complete isolation when requests originate simultaneously from Web and Mobile viewports, **Optimistic Locking** is implemented.
* The `version_id` integer tracks entity revisions on `expenses` and `payments`.
* SQLAlchemy automates version matching on execution. If a race condition occurs, a `StaleDataError` exception triggers.
* The API interceptor converts this error into an `HTTP 409 Conflict` structured response, prompting the client (WatermelonDB) to re-synchronize state cleanly.

---

## 5. Security & Isolation Architecture
* **Authentication:** Stateless JWT paradigm. Short-lived Access Tokens (15 minutes payload validation) combined with long-lived secure Refresh Tokens (rotated upon utilization).
* **Aisles of Isolation:** Row-Level/Owner Isolation. Every repository query dynamically merges the verified context `user_id` extracted from the cryptographically signed JWT into the SQLAlchemy `WHERE` clause.
* **CORS:** Dynamically provisioned cross-origin middleware mapped strictly through environment variables.

---

## 6. Resiliency, Idempotency & Caching (Redis Layer)
A standalone Redis instance acts as our high-performance scaling barrier:
* **Idempotency Middleware:** Mutating routes (`POST`) mandate an `Idempotency-Key` UUID header. Redis tracks keys for a sliding window of 5 seconds. Duplicate transmissions receive cached payloads without mutating PostgreSQL twice.
* **Reactive Cache Invalidation:** The computationally intense `/projections/periods` responses are cached under a user-scoped key `user:{id}:projections`. Any mutating operation (`POST`, `PUT`, `DELETE`) on accounts, expenses, payments, or bills executes an immediate cache purge (`DEL`) to guarantee real-time analytical consistency.

---

## 7. Observability & Configuration Standards
* **Structured Logs:** Utilizing `structlog` to emit uniform, line-by-line JSON streams directly to `stdout`. Context-aware parameters like `user_id`, `request_id`, and exception stack details are injected automatically via middleware.
* **Fail-Fast Configuration:** Integrated using `pydantic-settings`. Environmental parsing checks types and strict variable constraints on startup, halting immediate container execution if misconfigured.

---

## 8. Testing Infrastructure
* **Isolation Matrix:** Testing workflows run against a separate, independent database instance container (`postgres_test`).
* **Transaction Controls:** Every individual test runs within an isolated transactional session block. Pytest issues an unconditional `ROLLBACK` during teardown, maintaining an untainted database state without dropping tables sequentially.
* **Coverage Policy:** Unit test coverage minimum threshold is **80%**. Coverage reporting must include a dedicated configuration file that explicitly excludes non-actionable files (generated code, bootstrap files, and environment-specific wrappers) from threshold evaluation.
* **Granular Layout & Specification Architecture:**
    * `tests/unit/`: Mirroring `src/` hierarchy to test isolated algorithmic domains (e.g., Subscription dynamic flight simulation).
    * `tests/api/v1/`: Granular HTTP integration test scenario files matching 1-to-1 with Markdown specification documents in `docs/integration_tests/` (1 scenario = 1 `.py` file ↔ 1 `.md` file, e.g., `tests/api/v1/test_bill_delete_issue_ok.py` ↔ `docs/integration_tests/test_bill_delete_issue_ok.md`).
    * `docs/integration_tests/`: Human- and AI-readable Markdown specifications detailing test metadata, endpoints, preconditions, JSON request bodies, execution steps, expected status codes, and edge case handling.
    * **Language Policy:** All test files, code comments, docstrings, and specification documents must be strictly written in English.

---

## 9. Infrastructure Deployment Pipeline (DevOps/FinOps)
A pure serverless-container pipeline enforces stability without incurring continuous orchestration infrastructure costs.

### 9.1 Multi-Stage Docker Build
```dockerfile
# Stage 1: Build virtual environment utilizing uv
FROM ghcr.io/astral-sh/uv:python3.11-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime Minimal Image
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY src/ /app/src
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.2 Automated GitHub Actions Workflow
* **CI Pipeline (`Pull Request` to `stage` / `main`):** Executes formatting/linting sweeps in milliseconds using `ruff`, typechecks structural signatures using `mypy`, and launches the full suite of asynchronous integration tests via `pytest`.
* **Dev Integration Gate (`dev` branch):** Integration test suites are also executed in `dev` through a controlled manual or label-based trigger, enabling early full-flow validation without enforcing constant execution on every commit.
* **CD Pipeline (`Push` to `stage`):** Rebuilds the highly optimized multi-stage production image, ships it over secure SSH channels to the cloud testing box, and re-initializes the instance using `docker compose up -d --build`.

---

## 10. Repository Governance & Delivery Workflow
* **Branching Strategy:**
    * `dev`: Active implementation branch for all feature work.
    * `stage`: Pre-release validation and staging gate.
    * `main`: Production-ready stable releases only.
* **Promotion Flow:** `dev` -> `stage` -> `main`.
* **Commit Standard:** All commits must follow the **Conventional Commits** specification.
* **Implementation Rule:** Work is executed in atomic feature slices; each slice must include unit tests and corresponding documentation updates when applicable.
* **Execution Rule:** A feature slice is not allowed to progress to the next slice until the current slice is approved and committed.