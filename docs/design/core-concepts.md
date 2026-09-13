# CBX Core — Core concepts and definitions

## Terms

| Term | Definition |
|---|---|
| **Resource** (node) | A unit of infrastructure tracked as a graph node. Has a core id, a generic type, a provider binding, attributes, and edges. |
| **Type** | A generic, provider-neutral category of resource, e.g. `ComputeNode`. Defined by the core schema. Adding a type is a schema change. |
| **Attribute** | A named value on a node or edge. Two layers: *normalized* attributes defined by the type (same name and meaning across providers) and *native* attributes (an opaque provider-specific map the core stores but does not interpret). |
| **Relationship** (edge) | A typed, directed link between two nodes, e.g. `RUNS_IN`. May carry attributes. |
| **Provider** | The system hosting the resource: `aws`, `gcp`, `azure`, `kubernetes`, `onprem`, ... |
| **Provider binding** | Attributes tying a generic node to its real counterpart: provider, native type (`aws:ec2:instance`), native id (ARN, self-link, UID), region, native attribute map. |
| **Scope** | The administrative container a resource lives in: account, project, subscription, cluster. Scopes are nodes. Region and availability zone are attributes. |
| **Source** | The importer that asserted a node, edge or attribute, and when it last saw it. Every fact carries its source. |
| **Origin** | Whether a fact is *declared* (intent, e.g. Terraform) or *observed* (provider's live API). One resource may have both. |
| **Importer** | Extension that reads an external system and writes nodes and edges into the core in core vocabulary. |
| **Exporter** | Extension that reads the core through the API and produces something for an external system. Side effects happen in the exporter, never in the core. |
| **Schema** | Catalog of types, their normalized attributes, edge types, and allowed (from-type, edge, to-type) triples. Versioned, queryable through the API. |

## Node versus attribute

A thing is a **node** only if it meets at least two of:

1. **Independent lifecycle.** Can be created or deleted separately from what it is attached to.
2. **Shared.** More than one resource can reference it.
3. **Addressable.** An external tool needs to point at it on its own.
4. **Traversal-relevant.** A dependency question passes through it.

Everything else is an attribute of the nearest node, or is not stored.

| Thing | Verdict |
|---|---|
| VM / instance | Node |
| Network interface, private IP, public IP | Attribute of the compute node |
| Subnet | Node |
| Route table, routes, NACL | Attribute of the network, or not stored |
| Switch, router, firewall | Node (`NetworkDevice`); ports and VLAN tables are attributes |
| Security group | Node; individual rules are attributes |
| Block volume | Node |
| IAM role / service account | Node; policies are attributes |
| Tags / labels | Attribute |
| Kubernetes cluster | Node; pods and workloads not stored |
| Managed database instance | Node; schemas, tables, users not stored |
| DNS zone | Node; records are attributes |
| Load balancer | Node; listeners and target groups are attributes |
| Object storage bucket | Node; objects not stored |

## What every node carries

- `id` — core-assigned, stable, opaque.
- `type` — a generic type.
- `name` — human-readable.
- Provider binding: `provider`, `native_type`, `native_id`, `region` (nullable), `native` (map).
- `tags` — key/value map from the provider's tags or labels.
- `sources[]` — importer, origin, first seen, last seen.
- `created_at`, `updated_at`.

Every edge carries `type`, `sources[]`, timestamps, optional attributes.

(`provider`, `native_id`) is the natural key importers upsert by. The core `id` is what
exporters reference.

## Extension rules

- Importers map native types to generic types themselves and keep `native` verbatim.
- Importers use only edge types defined in the schema. `DEPENDS_ON` with a `reason` attribute is
  the fallback when no specific edge fits.
- Importer runs are idempotent: unchanged input produces no changes.
- Exporters go through the API, never the database.