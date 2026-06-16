# Project Tasks

This file tracks all implementation work as atomic feature slices.

## Status Legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Done

## Phase 1: Governance Baseline

- [x] Align architecture document with approved governance decisions.
- [x] Create professional README with roadmap and Mermaid diagrams.
- [x] Define execution gates and manual validation policy.
- [x] Establish persistent task and subtask tracking.

## Phase 2: Bootstrap with uv

- [ ] Initialize Python project metadata and dependency groups.
- [ ] Pin latest stable dependencies and generate lockfile.
- [ ] Configure ruff, mypy, pytest, pytest-asyncio, and httpx.
- [ ] Configure coverage threshold to 80% with explicit exclusions.
- [ ] Add smoke unit tests for application import/startup.
- [ ] Update README setup section.

## Phase 3: Application Skeleton (5 Layers + API v1)

- [ ] Create `src` package and modular folder layout.
- [ ] Implement root application factory.
- [ ] Register API routers under `/api/v1`.
- [ ] Add dependency wiring scaffold (`get_db -> repository -> service -> controller`).
- [ ] Add unit tests for app wiring and route registration.
- [ ] Update README architecture section if needed.

## Phase 4: Settings and Environment Hardening

- [ ] Implement typed configuration using pydantic-settings.
- [ ] Separate dev/test/prod behavior.
- [ ] Enforce startup fail-fast validation.
- [ ] Add unit tests for configuration behavior.
- [ ] Update README environment matrix.

## Phase 5: Logging and Error Contract

- [ ] Integrate structured JSON logging with structlog.
- [ ] Add request correlation context fields.
- [ ] Implement unified API error contract mapping.
- [ ] Add unit tests for error payload schema.
- [ ] Add unit tests for logging context enrichment.
- [ ] Update README observability section.

## Phase 6: Async DB and Alembic Foundation

- [ ] Configure SQLAlchemy async engine/session.
- [ ] Add declarative base and shared model mixins.
- [ ] Initialize Alembic migration environment.
- [ ] Add unit tests for DB session and metadata baseline.
- [ ] Update README migration workflow.

## Phase 7: Auth and Security Core

- [ ] Implement password hashing strategy.
- [ ] Implement access token issuance flow.
- [ ] Implement refresh token flow.
- [ ] Add auth dependencies for protected endpoints.
- [ ] Add unit tests for token lifecycle and invalid token handling.
- [ ] Update README auth flow.

## Phase 8: Owner Isolation Enforcement

- [ ] Inject authenticated `user_id` context across data access.
- [ ] Enforce owner filters in repositories.
- [ ] Add negative tests for cross-user access attempts.
- [ ] Update README data isolation section.

## Phase 9: Users, Profiles, Categories Feature

- [ ] Implement models/repository/service/controller/routes.
- [ ] Implement business validations.
- [ ] Add full unit tests for service/controller/repository behavior.
- [ ] Update README endpoint catalog.

## Phase 10: Accounts and Credit Cards Feature

- [ ] Implement polymorphic account persistence.
- [ ] Implement credit card domain rules.
- [ ] Add unit tests for polymorphic behavior and validations.
- [ ] Update README with data model diagram.

## Phase 11: Expenses, Payments, Optimistic Locking Feature

- [ ] Implement expenses STI model behavior.
- [ ] Implement payments lifecycle and uniqueness rules.
- [ ] Implement optimistic locking conflict handling (`409`).
- [ ] Add unit tests for concurrency and financial calculations with `Decimal`.
- [ ] Update README concurrency section.

## Phase 12: Bills Master-Detail Feature

- [ ] Implement bill services aggregate behavior.
- [ ] Implement bill issue monthly processing behavior.
- [ ] Add unit tests for period validation and duplicate prevention.
- [ ] Update README billing flow documentation.

## Phase 13: Projection Engine Feature

- [ ] Implement X-month projection endpoint.
- [ ] Implement dynamic installment/subscription simulation.
- [ ] Add unit tests for projection correctness and edge cases.
- [ ] Update README projection examples.

## Phase 14: Redis Idempotency Feature

- [ ] Implement idempotency middleware for mutating endpoints.
- [ ] Implement response replay strategy with expiration.
- [ ] Add unit tests for duplicate request protection and expiration.
- [ ] Update README idempotency contract.

## Phase 15: Projection Cache and Invalidation Feature

- [ ] Implement user-scoped Redis projection cache.
- [ ] Implement reactive invalidation after domain mutations.
- [ ] Add unit tests for cache hit/miss/invalidation behavior.
- [ ] Update README cache strategy.

## Phase 16: Background Tasks Feature

- [ ] Implement lightweight post-response tasks.
- [ ] Add safeguards for task failure visibility.
- [ ] Add unit tests for non-blocking execution behavior.
- [ ] Update README async task section.

## Phase 17: Final Integration Test Stage

- [ ] Build integration test suite for full domain flows.
- [ ] Configure isolated test database transaction strategy.
- [ ] Validate end-to-end flow from auth to projections.
- [ ] Configure dev manual/label trigger for integration tests.
- [ ] Update README test execution guide.

## Phase 18: Containerization and CI/CD

- [ ] Implement multi-stage Dockerfile using uv.
- [ ] Implement docker compose topology (app, postgres, redis).
- [ ] Implement GitHub Actions CI workflow for quality gates.
- [ ] Implement GitHub Actions integration workflow trigger strategy.
- [ ] Implement promotion-aware delivery flow.
- [ ] Update README deployment section.

## Phase 19: Documentation Finalization

- [ ] Consolidate final architecture references and decision records.
- [ ] Expand operational troubleshooting playbook.
- [ ] Add final Mermaid diagrams for runtime and release flows.
- [ ] Final editorial and consistency pass.
