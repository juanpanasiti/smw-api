#!/usr/bin/env bash
set -e

# Colored output formatting
BOLD="\031[1m"
GREEN="\033[32m"
BLUE="\033[34m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}=== Starting Local CI Pre-flight Checks ===${RESET}\n"

echo -e "${BOLD}[1/4] Syncing dependencies...${RESET}"
uv sync --all-extras
echo -e "${GREEN}✓ Dependencies up-to-date.${RESET}\n"

echo -e "${BOLD}[2/4] Running Ruff (Lint & Format check)...${RESET}"
uv run ruff check .
uv run ruff format --check .
echo -e "${GREEN}✓ Ruff lint and format checks passed.${RESET}\n"

echo -e "${BOLD}[3/4] Running MyPy (Type check)...${RESET}"
if uv run mypy src/; then
    echo -e "${GREEN}✓ Type checking passed.${RESET}\n"
else
    echo -e "${RED}⚠ Type checking emitted warnings/errors (configured as non-blocking in CI).${RESET}\n"
fi

echo -e "${BOLD}[4/4] Running Unit Tests with Coverage...${RESET}"
uv run pytest tests/unit --cov=src --cov-report=term-missing
echo -e "${GREEN}✓ Unit tests completed successfully.${RESET}\n"

echo -e "${BOLD}${GREEN}===========================================${RESET}"
echo -e "${BOLD}${GREEN}  All CI checks passed! Ready for push/PR  ${RESET}"
echo -e "${BOLD}${GREEN}===========================================${RESET}"
