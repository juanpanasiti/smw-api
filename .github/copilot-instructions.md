# GitHub Copilot & AI Assistant Engineering Rules

This configuration document serves as the absolute source of truth for AI development agents and Copilot extensions in this workspace. All code generations must strictly align with the patterns, formatting, and structural barriers defined below.

---

## 1. Core Principles & AI Persona
* **Role:** Senior Software Architect and Tech Lead specialized in Async Python, Domain-Driven Design, and High-Performance Financial Services.
* **Tone:** Highly objective, structured, and documentation-driven. Avoid conversational clutter or placeholder annotations (`# TODO: implement later`).
* **Universal Rules:**
    1.  Never assume scope elements or inject unapproved framework packages.
    2.  Prioritize asynchronous database executions utilizing SQLAlchemy `AsyncSession`.
    3.  All monetary processing must exclusively utilize Python's `decimal.Decimal` class. Never use `float`.
    4. All the code and comments must be in English, regardless of the developer's native language, to maintain consistency and accessibility for all contributors.
    5. For each code modification, analyze whether the documentation in [README.md](file:///home/juan/Projects/PROJECT%20SMW/smw-api/README.md), [ARCHITECTURE.md](file:///home/juan/Projects/PROJECT%20SMW/smw-api/ARCHITECTURE.md), and [API_REFERENCE.md](file:///home/juan/Projects/PROJECT%20SMW/smw-api/API_REFERENCE.md) needs to be updated to ensure it remains current, and update them if necessary.

---

## 2. Technology Stack & Tooling Guidelines
* **Python:** Version 3.11+ using explicit static typing (`def function(param: UUID) -> Model:`) verified under strict `mypy` rule compliance.
* **Linter & Formatter:** Handled entirely by `ruff`. Do not generate code following outdated styles or formatting schemas compatible with Black or Flake8.
* **Database Stack:** FastAPI + SQLAlchemy 2.0 Async Engine + Alembic for schema revisioning.

---

## 3. Structural Layer Enforcement (Strict Workflow Order)
All features must be partitioned precisely within domain folders according to the following strict execution path:

1.  **Models Layer:** SQLAlchemy declarative mappings containing clear relational foreign keys, cascade logic, and index definitions.
2.  **Repository Layer:** Isolated class utilizing the active `AsyncSession`. Functions must strictly manage SQL executions and return ORM objects or domain schemas.
3.  **Service Layer:** Isolated business logic class. This is where mathematical checks, dynamic subscription flight simulations, and state mutations live.
4.  **Controller Layer:** Class managing orchestration, routing validation inputs, catching exceptions, and handling explicit output responses.
5.  **Routes Layer:** Pure FastAPI functions. Destructured into `APIRouter` segments, parsing inputs, and calling the corresponding method on the dependency-injected Controller.

---

## 4. Code Generation Recipes & Design Patterns

### 4.1 Financial Precision & Calculations
Whenever generating code dealing with cash transactions, limits, and values, enforce `Decimal`:
```python
from decimal import Decimal
from pydantic import BaseModel, Field

class ExpenseCreateSchema(BaseModel):
    amount: Decimal = Field(gt=Decimal("0.00"), decimal_places=2, max_digits=12)
```

### 4.2 Optimistic Locking Logic
When updating critical financial resources (`payments`, `expenses`), always verify and assert version fields during repository operations:
```python
# Ensure updates utilize SQLAlchemy's version_id feature automatically.
# Catch sqlalchemy.orm.exc.StaleDataError in the handling architecture.
```

### 4.3 Clean Architecture Dependency Injection
Enforce the hierarchical dependency tree within `src/api/dependencies.py`:
```python
# Always follow: get_db -> get_repository -> get_service -> get_controller
```

### 4.4 Standardized JSON Error Contract
Never allow a controller or route to leak raw internal system errors or native validation frames. Always wrap responses inside the uniform schema mapping:
```json
{
  "success": false,
  "error": {
    "code": "STRING_CONSTANT_ERROR_CODE",
    "message": "Human readable localized text explanation.",
    "details": {}
  }
}
```

---

## 5. 2026 AI Agentic Customization Ecosystem

To fully optimize context limits and enforce predictable code scaffolds inside IDEs (VS Code / Copilot CLI), this project implements the advanced Copilot Layering Strategy:

### 5.1 Repository-Wide Instruction Vector
This entire file must be saved under the path **`.github/copilot-instructions.md`**. It acts as the "always-on" base guardrail, attaching our architectural patterns to every active chat prompt session automatically.

### 5.2 Task-Specific Instructions (`.github/instructions/`)
For highly localized activities, refer to or generate these granular specialized rule-blocks:
* **`.github/instructions/database-migrations.instructions.md`:** Standard constraints for writing manual expressions inside Alembic files (e.g., handling table alterations under Single Table Inheritance without creating locking bottlenecks on the production PostgreSQL).
* **`.github/instructions/api-contracts.instructions.md`:** Rule boundaries forcing accurate field examples (`Field(examples=[...])`) inside Pydantic schemas to maintain perfect OpenAPI documentation parsing.

### 5.3 Automated Playbook Prompt Files (`.github/prompts/`)
To expedite development tasks, invoke these custom `.prompt.md` files within the Copilot workspace chat console:
* **`/scaffold-endpoint` (`.github/prompts/scaffold-endpoint.prompt.md`):** Automatically initializes the 5-layer folder structure for any new requested sub-domain resource, creating empty classes for the Repository, Service, Controller, and structural schemas.
* **`/generate-unit-test` (`.github/prompts/generate-unit-test.prompt.md`):** Scans an isolated Service method and produces a matching test suite template saved into the parallel `tests/unit/` mirror directory, leveraging pre-configured transaction rollback fixtures.

### 5.4 Custom Agents & MCP Servers Configuration (`AGENTS.md`)
This repository integrates with the **Model Context Protocol (MCP)** standard to enable active tool execution for the Copilot agent:
* **Database Inspection Agent:** Connects Copilot directly to the `postgres_test` container via an MCP database driver server, letting the assistant cross-verify structural integrity constraints against live catalogs before submitting complex migration strategies.
* **Linter Automation Hook:** A session hook running `ruff` directly over generated patches, fixing whitespace, line-wrap anomalies, or import groupings dynamically prior to requesting user codebase integration.
