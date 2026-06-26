# Personal Finance API

> A high-performance, production-ready RESTful API for personal finance management, credit card tracking, and forward-looking financial projections.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-red)](https://docs.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io/)
[![uv](https://img.shields.io/badge/uv-package%20manager-6E56CF)](https://docs.astral.sh/uv/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Running the API](#running-the-api)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Docker](#docker)
- [Project Structure](#project-structure)
- [API Reference](./API_REFERENCE.md)

---

## Overview

The Personal Finance API handles:

- **Accounts** — Polymorphic account model supporting credit cards (with extension cards) and standard accounts.
- **Expenses & Payments** — Single Table Inheritance for purchases (installment-based) and subscriptions, with full payment lifecycle tracking and optimistic locking.
- **Bills & Services** — Master-detail module for recurring utility/service bills (e.g., electricity, internet).
- **Financial Projections** — Monthly projections computing income, total expenses, pending bills, and per-card credit usage with a reactive Redis cache layer.
- **Idempotency** — All mutating endpoints require an `Idempotency-Key` header, backed by a 5-second Redis sliding window to prevent double-submissions.

---

## Architecture

```text
[HTTP Request] ──► Routes ──► Controller ──► Service ──► Repository ──► SQLAlchemy Model
                                    │                                           │
                                    └─── Redis (Cache & Idempotency) ───────── PostgreSQL
```

### Core Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ with strict static typing |
| Web Framework | FastAPI (async event-loop first) |
| ORM & Migrations | SQLAlchemy 2.0 Async + Alembic |
| Primary Database | PostgreSQL 15 |
| Cache & Idempotency | Redis 7 |
| Package Manager | `uv` |
| Linter / Formatter | `ruff` |
| Testing | `pytest` + `httpx` (async) |

---

## Prerequisites

Before you start, make sure you have the following installed:

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| `uv` | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | V2 (`docker compose`) | Bundled with Docker Desktop |

---

## Local Development Setup

### Step 1 — Clone the repository

```bash
git clone <repository-url>
cd smw-api
```

### Step 2 — Configure environment variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

> See the [Environment Variables](#environment-variables) section for a full reference.

### Step 3 — Spin up infrastructure services

Start PostgreSQL and Redis in the background using Docker Compose:

```bash
docker compose up -d
```

Verify all containers are healthy:

```bash
docker compose ps
```

Expected output:

```
NAME              STATUS
smw_postgres      Up (healthy)
smw_postgres_test Up (healthy)
smw_redis         Up (healthy)
```

### Step 4 — Install dependencies

```bash
uv sync
```

### Step 5 — Run database migrations

Apply all Alembic migrations to create the schema:

```bash
uv run alembic upgrade head
```

### Step 6 — Start the development server

```bash
uv run uvicorn src.main:app --reload
```

The API will be available at **http://localhost:8000**.

---

## Environment Variables

Create a `.env` file at the project root. All variables are read at startup by `pydantic-settings` — the application will **refuse to start** if any required variable is missing or has an invalid type.

```dotenv
# ─── PostgreSQL ───────────────────────────────────────────────
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=smw_api_dev
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432

# ─── Redis ────────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
```

> **Note:** The `docker-compose.yml` already sets these defaults so a fresh `.env` copy will work out of the box for local development.

---

## Database Migrations

This project uses **Alembic** for schema versioning. All migrations live in `migrations/versions/`.

| Command | Description |
|---|---|
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic downgrade -1` | Roll back the last migration |
| `uv run alembic current` | Show the current database revision |
| `uv run alembic history` | List all migration revisions |
| `uv run alembic revision --autogenerate -m "description"` | Generate a new migration from model changes |

---

## Running the API

### Development (with hot-reload)

```bash
uv run uvicorn src.main:app --reload
```

### Production-like (without reload)

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API Documentation

FastAPI generates interactive documentation automatically. Once the server is running:

| Interface | URL |
|---|---|
| **Swagger UI** (interactive) | http://localhost:8000/docs |
| **ReDoc** (reference) | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

> 📄 For the full endpoint reference including request/response schemas, field constraints, error codes, and examples, see **[API_REFERENCE.md](./API_REFERENCE.md)**.

### Authentication

All endpoints (except `/api/v1/auth/register` and `/api/v1/auth/login`) require a Bearer token.

**1. Register a user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123!",
    "profile": {
      "first_name": "John",
      "last_name": "Doe",
      "birthdate": "1990-01-15",
      "monthly_spending_limit": "3000.00"
    }
  }'
```

**2. Login to obtain tokens:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPass123!"
```

**3. Use the access token:**
```bash
curl http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer <access_token>"
```

### Idempotency

All `POST`, `PATCH`, and `DELETE` endpoints require an `Idempotency-Key` header containing a unique UUID. Duplicate requests within a 5-second window return the cached response without re-executing the operation.

```bash
-H "Idempotency-Key: $(uuidgen)"
```

---

## Testing

The project has two test tiers:

| Suite | Path | Description |
|---|---|---|
| **Unit** | `tests/unit/` | Isolated service logic tests using `AsyncMock` — no real DB required |
| **Integration** | `tests/api/v1/` | Full E2E HTTP tests against a real PostgreSQL + Redis instance |

### Run unit tests only (no Docker needed)

```bash
uv run pytest tests/unit/ -v
```

### Run the full test suite (requires Docker)

First, start the test infrastructure:

```bash
docker compose up -d
```

Then run all tests with coverage:

```bash
uv run pytest --cov=src --cov-report=term-missing -v
```

The integration tests automatically:
- Create all database tables before the session.
- Wrap each test in a **transaction that is rolled back** after completion — the database is never permanently mutated.
- Override the FastAPI dependency for `db_session` to use the test connection.

### Linting and formatting

```bash
# Check for lint errors
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

---

## Docker

### Build the production image

The `Dockerfile` uses a **multi-stage build** to produce a minimal runtime image:

```bash
docker build -t smw-api:latest .
```

### Run the production container

```bash
docker run -p 8000:8000 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=smw_api_dev \
  -e POSTGRES_SERVER=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  smw-api:latest
```

---

## Project Structure

```
smw-api/
├── src/
│   ├── api/
│   │   ├── dependencies.py        # DI wiring: DB → Repo → Service → Controller
│   │   └── routes_classes.py      # IdempotentRoute custom APIRoute class
│   ├── controllers/               # HTTP orchestration layer
│   ├── core/
│   │   ├── config.py              # pydantic-settings configuration
│   │   ├── database.py            # AsyncEngine & session factory
│   │   ├── redis.py               # Redis client & cache invalidation helpers
│   │   └── security.py            # JWT creation & password hashing
│   ├── models/                    # SQLAlchemy declarative models
│   ├── repositories/              # Data access layer (SQL only, no business logic)
│   ├── routes/                    # FastAPI APIRouter endpoint definitions
│   ├── schemas/                   # Pydantic I/O schemas
│   ├── services/                  # Business logic layer
│   └── main.py                    # FastAPI app factory & router registration
├── migrations/                    # Alembic migration scripts
│   └── versions/
├── tests/
│   ├── unit/                      # Isolated unit tests (AsyncMock)
│   └── api/v1/                    # Integration tests (real DB + Redis)
├── .github/workflows/ci.yml       # GitHub Actions CI pipeline
├── docker-compose.yml             # Local development services
├── docker-compose.test.yml        # Isolated test services
├── Dockerfile                     # Multi-stage production image
├── pyproject.toml                 # Project metadata, dependencies & tool config
├── ARCHITECTURE.md                # Full technical architecture reference
└── README.md
```

---

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every Pull Request to `dev`, `stage`, and `main`:

1. **Lint** — `ruff check .`
2. **Format check** — `ruff format --check .`
3. **Type check** — `mypy src/`
4. **Full test suite** — `pytest --cov=src --cov-fail-under=70`

Services (PostgreSQL + Redis) are spun up as GitHub Actions service containers so integration tests run without any external dependencies.
