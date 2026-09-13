# CBX Core — Research summary

Researched 2026-09-12.

## Existing projects and abstractions to borrow

| Project | What it is | What CBX Core borrows | What it does not borrow |
|---|---|---|---|
| **Cartography** (CNCF) | Python tool that pulls assets from 30+ platforms into Neo4j | `id` / `firstseen` / `lastupdated` on every node with a stale sweep after each sync; "ontology" labels that map provider nodes to generic ones (AWSACMCertificate → Certificate); typed relationship names (`PART_OF_SUBNET`, `EXPOSE`, `ASSUMES`) | Schema is provider-first (AWSEC2Instance is the primary label); ours is generic-first with a provider binding |
| **OCCI** (Open Grid Forum, Open Cloud Computing Interface) | Standard core model: Kinds `Compute`, `Storage`, `Network`; Links `NetworkInterface`, `StorageLink`; Mixins for provider extension | Three-kind minimal vocabulary; the mixin idea maps to our normalized-plus-native attribute layering | Models NIC as a first-class link; we chose attribute |
| **TOSCA Simple Profile** (OASIS) | Normative node types (`Compute`, `BlockStorage`, `Network`, `Database`, `LoadBalancer`) and relationships (`HostedOn`, `ConnectsTo`, `DependsOn`) | Naming of generic types; a small normative set with a `Root` type all others derive from; `DependsOn` as the generic fallback edge | Orchestration, requirements/capabilities matching, deployment lifecycle |
| **OpenTelemetry resource semantic conventions** | Standard attribute names: `cloud.provider`, `cloud.account.id`, `cloud.region`, `cloud.availability_zone`, `cloud.platform`, `host.id`, `container.id`, `faas.name`, `k8s.cluster.name` | Attribute naming for the provider binding, so a monitoring exporter can emit compatible tags without translation | A tagging convention, not a graph model |
| **Backstage system model** | Entity kinds Component / API / Resource / System / Domain with `ownedBy`, `partOf`, `dependsOn` | Entity envelope shape (kind, metadata, spec, relations); explicit entity-versus-attribute reasoning | Application/service catalog concerns |
| **Infrahub** (OpsMill) | Neo4j-backed infrastructure source of truth with YAML schema, per-attribute lineage (`source`, `owner`, `is_protected`), branching and merging | Per-fact lineage metadata; schema as versioned data rather than hard-coded | Branching/diff/merge of the database; network-centric scope |
| **CloudQuery / Steampipe** | Sync (CloudQuery) or live-query (Steampipe) cloud APIs into SQL tables, one table per native type | Plugin architecture with a clear source/destination split | Tables mirror native APIs one-to-one; no generic model |
| **Cloud provider inventories** (AWS Config, GCP Cloud Asset Inventory, Azure Resource Graph) | Native single-provider inventories with relationship types and change feeds | Change feed and stale detection ideas; natural data sources for observed importers | Single provider each |
| **Wiz Security Graph** | Commercial cloud security graph: nodes grouped into Resources, Identities, Workloads, Data | Four top-level groupings as a sanity check on our type set | Security findings, exposure analysis |
| **Cloud Property Graph** (Fraunhofer AISEC, 2022), **Unified Cloud Resource Ontology** (2026, from Terraform provider schemas) | Academic vendor-independent cloud ontologies | Validation of "generic type + provider mapping"; possible source for native-to-generic mapping tables | Security-assessment focus |

## Sources

- [Cartography schema](https://docs.cartography.dev/usage/schema.html), [Cartography AWS schema](https://docs.cartography.dev/modules/aws/schema.html), [Cartography repo](https://github.com/cartography-cncf/cartography)
- [TOSCA Simple Profile YAML v1.3](https://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.3/TOSCA-Simple-Profile-YAML-v1.3.html), [TOSCA and OCCI model-based resource management](https://arxiv.org/pdf/2001.07900)
- [OpenTelemetry resource semantic conventions](https://opentelemetry.io/docs/specs/semconv/resource/), [Cloud resource semantic conventions explainer](https://oneuptime.com/blog/post/2026-02-06-cloud-resource-semantic-conventions-aws-gcp-azure/view)
- [Backstage system model](https://backstage.io/docs/features/software-catalog/system-model/), [Backstage system model RFC](https://github.com/backstage/backstage/issues/390)
- [Infrahub overview](https://docs.infrahub.app/overview), [Infrahub schema FAQ](https://opsmill.com/blog/infrahub-schema-faqs/)
- [CloudQuery vs cloud asset inventory tools](https://www.cloudquery.io/blog/cloudquery-vs-cloud-asset-inventory-tools), [Steampipe vs CloudQuery](https://www.cloudquery.io/blog/steampipe-vs-cloudquery)
- [GCP Cloud Asset Inventory relationship types](https://docs.cloud.google.com/asset-inventory/docs/relationship-types), [AWS Config vs Azure Resource Graph vs GCP Asset Inventory](https://cloudcomparetool.com/blog/aws-config-vs-azure-resource-graph-vs-google-cloud-asset-inventory)
- [Wiz Security Graph](https://www.wiz.io/lp/wiz-security-graph), [Recreating Wiz's graph with PuppyGraph](https://www.puppygraph.com/blog/wiz-security-graph)
- [Cloud Property Graph paper](https://arxiv.org/abs/2206.06938), [Toward a Unified Cloud Resource Ontology for Multicloud Security](https://link.springer.com/article/10.1134/S1054661826700367)
- [Cloud CMDB vs traditional CMDB](https://www.joekarlsson.com/blog/cloud-cmdb-vs-traditional-cmdb-2026/)