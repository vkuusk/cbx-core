.PHONY: help install run run-fg run-stop test lint fmt db-up db-down db-nuke db-ui

# local overrides (copied from .env.default; gitignored); exported so the API,
# tests and compose all see the same values
-include .env
export

PORT := $(or $(CBX_PORT),2727)
URL  := http://127.0.0.1:$(PORT)

help:           ## list targets
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install:        ## create the venv and install dependencies
	uv sync

run: db-up      ## start the API in the background (log: sandbox/cbx-core.log)
	@mkdir -p sandbox
	@if curl -sf "$(URL)/api/health" >/dev/null 2>&1; then \
		echo "API already running at $(URL)"; \
	else \
		nohup uv run cbx-core >> sandbox/cbx-core.log 2>&1 & echo $$! > sandbox/cbx-core.pid; \
		for i in $$(seq 1 50); do curl -sf "$(URL)/api/health" >/dev/null 2>&1 && break; sleep 0.2; done; \
		curl -sf "$(URL)/api/health" >/dev/null 2>&1 || { echo "API did not start, see sandbox/cbx-core.log"; exit 1; }; \
		echo "API running at $(URL)"; \
	fi

run-fg: db-up   ## start the API in the foreground (Ctrl+C stops it)
	@if curl -sf "$(URL)/api/health" >/dev/null 2>&1; then \
		echo "API already running at $(URL) (make run-stop first)"; exit 1; fi
	uv run cbx-core

run-stop:       ## stop the background API
	@if [ -f sandbox/cbx-core.pid ] && kill $$(cat sandbox/cbx-core.pid) 2>/dev/null; then \
		echo "API stopped"; \
	else \
		echo "no background API to stop"; \
	fi; rm -f sandbox/cbx-core.pid

test: db-up     ## run all tests
	uv run pytest

lint:           ## ruff check and format check
	uv run ruff check src tests
	uv run ruff format --check src tests

fmt:            ## ruff format and autofix
	uv run ruff format src tests
	uv run ruff check --fix src tests

db-up:          ## start Neo4j in a container and wait until healthy
	docker compose up -d --wait neo4j

db-down:        ## stop the container (data volume survives)
	docker compose down

db-nuke:        ## stop the container and DELETE the data volume
	docker compose down -v

db-ui: db-up    ## open Neo4j Browser for the compose database
	@echo "Neo4j Browser: http://127.0.0.1:$(or $(CBX_NEO4J_HTTP_PORT),27474)  (user neo4j, password $(or $(CBX_NEO4J_PASSWORD),cbx-dev-password))"
	@open "http://127.0.0.1:$(or $(CBX_NEO4J_HTTP_PORT),27474)" 2>/dev/null || true