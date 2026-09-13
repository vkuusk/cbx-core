# CBX Core — Scope

## Summary

CBX Core is the central, provider-neutral inventory graph of an organization's infrastructure.
Resources are nodes, dependencies are edges, stored in a graph database and exposed through an
API. Node types are generic (compute node, network), with the provider-specific identity kept as
a binding on the node. Importers bring data in from tools such as cloud provider APIs and
Terraform; exporters read the graph to configure other systems such as monitoring. The core is
passive: it holds the shared picture of the infrastructure, and other tools act on it.

Concepts and terms are defined in [core-concepts.md](core-concepts.md).
Existing projects we borrow from are in [research-summary.md](research-summary.md).

## Out of scope

- Provisioning, configuring, or deleting infrastructure. No "apply", no drift remediation.
- Being a Terraform/Pulumi/Crossplane replacement or an orchestrator.

## Skeleton (first milestone)

One organization, one provider (AWS), one account, one region. The graph holds networks,
subnets and compute nodes.

Nodes:

| Type | AWS binding |
|---|---|
| `Organization` | none, root of the graph |
| `Scope` | AWS account |
| `Network` | VPC |
| `Subnet` | subnet |
| `ComputeNode` | EC2 instance |

Edges:

| Edge | From → To |
|---|---|
| `CONTAINS` | Organization → Scope, Scope → Network, Network → Subnet |
| `RUNS_IN` | ComputeNode → Subnet |

Workflows the skeleton must exercise end to end:

1. Importer: read VPCs, subnets and EC2 instances from one AWS account and region, upsert them
   into the graph by natural key, mark nodes the importer no longer sees as stale.
2. API: create, read, update, delete nodes and edges; list by type; traverse from a node along
   chosen edge types.
3. Exporter: read the graph through the API and produce an output for an external system
   (target system to be chosen when the skeleton is running).
4. Schema: list types, edge types and allowed (from, edge, to) triples through the API.

Everything beyond this list is added one feature at a time after the skeleton is reviewed.