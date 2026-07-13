# backfill-hell — one-command operations.
# On Windows: run inside Git Bash, or install make (`choco install make`).
# If you don't have make, the underlying commands are shown for each target.

.PHONY: up down logs ps fmt lint type test check backfill chaos reconcile

up:            ## Start Postgres + MinIO
	docker compose up -d
	@echo "Postgres :5432   MinIO API :9000   MinIO console :9001 (minioadmin/minioadmin)"

down:          ## Stop everything, keep volumes
	docker compose down

logs:          ## Follow container logs
	docker compose logs -f

ps:            ## Show container status
	docker compose ps

fmt:           ## Auto-format + autofix
	uv run ruff format .
	uv run ruff check --fix .

lint:          ## Lint only
	uv run ruff check .

type:          ## Strict type check
	uv run mypy

test:          ## Run the test suite
	uv run pytest -q

check: lint type test   ## Everything CI runs, locally

# --- Filled in later phases ---
backfill:      ## Phase 3+: run the historical backfill
	@echo "TODO — Phase 3"

chaos:         ## Phase 8: kill a worker mid-run, resume, prove zero-dup/zero-gap
	@echo "TODO — Phase 8"

reconcile:     ## Phase 6: generate the reconciliation report
	@echo "TODO — Phase 6"
