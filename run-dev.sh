#!/usr/bin/env bash
set -euo pipefail

# ── Helpers ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

info()    { echo -e "${CYAN}[dev]${NC} $*"; }
success() { echo -e "${GREEN}[dev]${NC} $*"; }
warn()    { echo -e "${YELLOW}[dev]${NC} $*"; }
error()   { echo -e "${RED}[dev]${NC} $*" >&2; }

# ── Cleanup on exit ────────────────────────────────────────────────────────────
COMPOSE_SERVICES=()

cleanup() {
    echo ""
    warn "Shutting down …"
    if [[ ${#COMPOSE_SERVICES[@]} -gt 0 ]]; then
        docker compose stop "${COMPOSE_SERVICES[@]}" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# ── Argument parsing ───────────────────────────────────────────────────────────
WITH_TESTS=false

for arg in "$@"; do
    case "$arg" in
        --tests) WITH_TESTS=true ;;
        --help|-h)
            echo -e "${BOLD}Usage:${NC} $0 [--tests]"
            echo ""
            echo "  (no flags)   Start dev infra (postgres + redis) and run the API"
            echo "  --tests      Also start postgres_test and redis_test containers"
            exit 0
            ;;
        *)
            error "Unknown flag: $arg"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

# ── Determine which Docker services to start ───────────────────────────────────
COMPOSE_SERVICES=(db redis)

if [[ "$WITH_TESTS" == true ]]; then
    COMPOSE_SERVICES+=(postgres_test redis_test)
    info "Mode: dev + test containers"
else
    info "Mode: dev containers only"
fi

# ── Start infrastructure ───────────────────────────────────────────────────────
info "Starting Docker services: ${COMPOSE_SERVICES[*]} …"
docker compose up -d --wait "${COMPOSE_SERVICES[@]}"
success "All containers are healthy."

# ── Run API (foreground, last command) ─────────────────────────────────────────
echo ""
info "Starting FastAPI with hot-reload  →  http://localhost:8000"
info "Docs                              →  http://localhost:8000/api/v1/openapi.json"
echo -e "${YELLOW}Press Ctrl+C to stop the server and shut down the containers.${NC}"
echo ""

uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
