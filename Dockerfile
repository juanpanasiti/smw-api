# ── Stage 1: Build virtual environment using uv ──────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential libc6-dev

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ── Stage 2: Runtime Minimal Image ───────────────────────────────────────────
FROM python:3.14-slim-bookworm AS runtime
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Application source code
COPY src/ /app/src/

# Alembic migrations
COPY alembic.ini /app/alembic.ini
COPY migrations/ /app/migrations/

# Entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Non-root user
RUN useradd -u 8888 appuser \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
