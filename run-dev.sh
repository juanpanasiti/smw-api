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
USE_DOCKER_API=false
BUILD_IMAGES=false
SYNC_ENV=false

for arg in "$@"; do
    case "$arg" in
        --tests) WITH_TESTS=true ;;
        --docker) USE_DOCKER_API=true ;;
        --build) BUILD_IMAGES=true ;;
        --sync) SYNC_ENV=true ;;
        --help|-h)
            echo -e "${BOLD}Usage:${NC} $0 [--tests] [--docker] [--build] [--sync]"
            echo ""
            echo "  (no flags)   Start dev infra (postgres + redis) and run the API locally via uv"
            echo "  --tests      Also start postgres_test and redis_test containers"
            echo "  --docker     Run the API inside Docker instead of locally"
            echo "  --build      Force build of Docker images (useful with --docker)"
            echo "  --sync       Run 'uv sync --all-extras' before starting"
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

if [[ "$USE_DOCKER_API" == true ]]; then
    COMPOSE_SERVICES+=(api)
    info "Mode: API will run inside Docker"
fi

# ── Sync environment ───────────────────────────────────────────────────────────
if [[ "$SYNC_ENV" == true ]]; then
    info "Syncing local environment and lockfile..."
    uv sync --all-extras
    success "Environment synced successfully."
    echo ""
fi

# ── Start infrastructure ───────────────────────────────────────────────────────
info "Starting Docker services: ${COMPOSE_SERVICES[*]} …"
UP_ARGS=("-d" "--wait")
if [[ "$BUILD_IMAGES" == true ]]; then
    UP_ARGS+=("--build")
    info "Building images before starting..."
fi

docker compose up "${UP_ARGS[@]}" "${COMPOSE_SERVICES[@]}"
success "All containers are healthy."

# ── Run API (foreground, last command) ─────────────────────────────────────────
echo ""
info "API  →  http://localhost:8000"
info "Docs →  http://localhost:8000/api/v1/openapi.json"
echo -e "${YELLOW}Press Ctrl+C to stop the server and shut down the containers.${NC}"
echo ""

if [[ "$USE_DOCKER_API" == true ]]; then
    info "Attaching to API container logs..."
    docker compose logs -f api
else
    info "Starting FastAPI locally with hot-reload..."
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
fi
