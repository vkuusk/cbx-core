# CBX Core — Architecture v1

Decisions made so far. Each item is a decision unless marked *pending*.

## Storage

- Graph database: Neo4j.

## Language and runtime

- Python.
- API framework: FastAPI, REST. Pydantic models define node and edge shapes and drive the
  OpenAPI schema.
- Neo4j access: official `neo4j` Python driver, async mode. No object-graph mapper. A thin
  repository module holds the parameterized Cypher queries.
- Packaging: uv.
- Tests: pytest against a real Neo4j (compose container or home lab), no database mocks.

## Web UI

- Preact with htm, one vendored ES module in `webui/vendor`, no build step and no node
  toolchain. Served by the API as static files at `/`.
- Hash-routed pages: Browse (tree) and Resource (create, edit, delete, edges).

## Source layout

```
src/cbx_core/   application code
tests/          tests
webui/          static web UI
docs/design/    design docs
sandbox/        local run logs and pid (gitignored)
```

## Local development

- Neo4j via docker compose, or the home-lab instance at `10.0.0.117`.
- Connection settings come from environment variables so both options work without code changes.