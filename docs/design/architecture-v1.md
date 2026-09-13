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
- Tests: pytest against a separate test Neo4j (compose service `neo4j-test`, no volume, own
  port), no database mocks. Tests never touch the working database.

## Schema

- `src/core/schema.py` is the single source of truth: providers, node types with their
  normalized attributes, edge types, allowed (from, edge, to) triples, and a one-line meaning
  for each. `GET /api/schema` serves it as-is; the web UI renders forms from it.
- Providers: `on-prem`, `aws`, `gcp`. For `on-prem`, `provider_id` is the inventory tag (the
  sticker on the device).
- `provider_type` is an enum: the schema lists the allowed values per provider and generic
  type (e.g. on-prem NetworkDevice: switch, router, firewall, access-point). The UI shows
  `provider_type` and `provider_id` as "type" and "id" under the provider row.
- The provider is chosen on a Scope and inherited by everything under it. Organization has no
  provider binding; the API rejects one.
- A write with no explicit `sources` is a manual inventory edit: the core stamps it with
  importer `inventory`, origin `declared`.

## Interfaces

- Core and officially supported interfaces live in this repo. Core is `src/core/`; each
  interface is a package under `src/interfaces/<name>/`.
- Every interface talks to the core only through the HTTP API, including the ones in this
  repo. No interface touches Neo4j.
- First interface: **inventory**, the web UI plus the API, for adding, editing and removing
  infrastructure by hand.

## Web UI

- Preact with htm, one vendored ES module in `webui/vendor`, no build step and no node
  toolchain. Served by the API as static files at `/`.
- Hash-routed pages: Browse (tree) and Resource (create, edit, delete, link, unlink).
- Swagger UI at `/api/docs`, OpenAPI document at `/api/openapi.json`.

## Source layout

```
src/core/         the core: API, schema, storage
src/interfaces/   official interfaces, one package each
tests/            tests
webui/            static web UI
docs/design/      design docs
docs/planning/    implementation plans
sandbox/          local run logs and pid (gitignored)
```

## Local development

- Neo4j via docker compose, or the home-lab instance at `10.0.0.117`.
- Connection settings come from environment variables so both options work without code changes.