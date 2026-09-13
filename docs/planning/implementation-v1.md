# Implementation plan v1

Ordered. Each step is reviewed in use before the next starts.

1. **Skeleton** — Neo4j, HTTP API (nodes, edges, schema, traversal), web UI, tests. Done.
2. **Inventory interface v1** — providers `on-prem`/`aws`/`gcp`, `NetworkDevice` and
   `SERVED_BY`, inventory source stamping, provider select and link control in the UI. Done.
3. **Home lab entered by hand** — Organization `vvkhome`, Scope `vvkhome-lab`, Network `LAN`,
   switches, subnets, hosts. Feedback from this drives the next steps.
4. **Schema growth from feedback** — attributes and types the home lab needs that the schema
   lacks; each addition justified against the node-versus-attribute rule.
5. **First importer** — AWS observed importer under `src/interfaces/`, talking to the HTTP API.
