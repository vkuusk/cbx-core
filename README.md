# cbx-core

Core of an infrastructure management ecosystem: a provider-neutral inventory graph of an
organization's infrastructure, stored in Neo4j and served through an HTTP API with a web UI.

Design docs: [scope](docs/design/scope.md), [core concepts](docs/design/core-concepts.md),
[architecture](docs/design/architecture-v1.md), [plan](docs/planning/implementation-v1.md).

## Run

Requires Docker, [uv](https://docs.astral.sh/uv/) and `make`.

```
make install      # venv and dependencies
make run          # Neo4j in a container + API in the background
make run-stop     # stop the API
make test         # tests, against a separate test Neo4j container
make help         # all targets
```

- Web UI: http://127.0.0.1:2727
- API reference (Swagger): http://127.0.0.1:2727/api/docs
- Neo4j Browser: `make db-ui`

To use another Neo4j, copy `.env.default` to `.env` and set `CBX_NEO4J_URI`, `CBX_NEO4J_USER`
and `CBX_NEO4J_PASSWORD`.

## Layout

```
src/core/         the core: API, schema, storage
src/interfaces/   official interfaces, one package each
webui/            static web UI (Preact + htm, no build step)
tests/
docs/
```
