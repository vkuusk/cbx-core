"""Graph schema: providers, node fields, node types with normalized attributes, edge types,
allowed triples.

The single source of truth for what the core can hold. Served as-is by GET /api/schema.
"""

PROVIDERS: dict[str, str] = {
    "on-prem": "Physical infrastructure you own.",
    "aws": "Amazon Web Services.",
    "gcp": "Google Cloud.",
}

# provider -> generic type -> allowed provider types -> what provider_id holds
PROVIDER_TYPES: dict[str, dict[str, dict[str, str]]] = {
    "on-prem": {
        "Scope": {"site": "site code, e.g. home"},
        "Network": {"lan": "LAN name", "vlan": "VLAN id"},
        "Subnet": {"subnet": "subnet name or VLAN id"},
        "NetworkDevice": {
            "switch": "inventory tag (sticker)",
            "router": "inventory tag (sticker)",
            "firewall": "inventory tag (sticker)",
            "access-point": "inventory tag (sticker)",
        },
        "ComputeNode": {
            "server": "inventory tag (sticker)",
            "mini-pc": "inventory tag (sticker)",
            "vm": "VM id or name on its host",
            "nas": "inventory tag (sticker)",
        },
    },
    "aws": {
        "Scope": {"account": "account id"},
        "Network": {"vpc": "vpc id"},
        "Subnet": {"subnet": "subnet id"},
        "NetworkDevice": {},
        "ComputeNode": {"ec2-instance": "instance id"},
    },
    "gcp": {
        "Scope": {"project": "project id"},
        "Network": {"vpc": "network self-link"},
        "Subnet": {"subnet": "subnetwork self-link"},
        "NetworkDevice": {},
        "ComputeNode": {"compute-instance": "instance id or self-link"},
    },
}

# fields every node has -> meaning
FIELDS: dict[str, str] = {
    "name": "Human-readable name.",
    "provider": "Where the resource lives. Chosen on the Scope, inherited by everything under it.",
    "provider_type": "The provider's own type for this resource, from the list for this provider.",
    "provider_id": "The provider's own identifier for this resource. Unique per provider.",
    "region": "Provider region or location label. Optional.",
    "tags": "Provider tags or labels, key=value per line.",
    "native": "Provider-specific attributes the core stores but does not interpret. JSON.",
}

# type -> meaning, normalized attributes (name -> meaning; values live in Node.attrs), and
# whether the type carries a provider binding. Scope declares the provider; everything under
# a Scope belongs to that provider.
TYPES: dict[str, dict] = {
    "Organization": {
        "description": "Root of the graph. No provider binding.",
        "attributes": {},
        "binding": False,
    },
    "Scope": {
        "description": "Declares a provider: cloud account, project, or a physical site.",
        "attributes": {"environment": "prod, stage, dev, lab, ..."},
    },
    "Network": {
        "description": "Routed network: VPC, VNet, or a LAN / VLAN.",
        "attributes": {"cidr": "Address range, e.g. 10.0.0.0/16."},
    },
    "Subnet": {
        "description": "Address range inside a network.",
        "attributes": {
            "cidr": "Address range, e.g. 10.0.1.0/24.",
            "availability_zone": "Zone inside the region, e.g. us-east-1a. Optional.",
        },
    },
    "NetworkDevice": {
        "description": "Physical or virtual switch, router, or firewall.",
        "attributes": {
            "model": "Vendor model, e.g. USW-24.",
            "management_ip": "Address of the management interface.",
        },
    },
    "ComputeNode": {
        "description": "VM, bare-metal host, or dedicated instance.",
        "attributes": {
            "instance_type": "Size class, e.g. t3.small, or the hardware model for a physical host.",
            "state": "running, stopped, ...",
            "image": "OS image or installed OS.",
            "private_ips": "Private addresses, comma separated.",
            "public_ips": "Public addresses, comma separated.",
        },
    },
}

EDGE_TYPES: dict[str, str] = {
    "CONTAINS": "Administrative containment.",
    "RUNS_IN": "Placement of a resource inside a network segment.",
    "SERVED_BY": "A network segment is provided by a network device.",
}

# (from type, edge type, to type)
TRIPLES: set[tuple[str, str, str]] = {
    ("Organization", "CONTAINS", "Scope"),
    ("Scope", "CONTAINS", "Network"),
    ("Network", "CONTAINS", "Subnet"),
    ("Network", "CONTAINS", "NetworkDevice"),
    ("ComputeNode", "RUNS_IN", "Subnet"),
    ("Subnet", "SERVED_BY", "NetworkDevice"),
}


def is_provider(name: str | None) -> bool:
    return name is None or name in PROVIDERS


def has_binding(type: str) -> bool:
    return TYPES[type].get("binding", True)


def provider_types(provider: str | None, type: str) -> list[str]:
    return list(PROVIDER_TYPES.get(provider, {}).get(type, {}))


# a provider type is required when the provider offers any for this generic type
def is_provider_type(provider: str | None, type: str, provider_type: str | None) -> bool:
    allowed = provider_types(provider, type)
    return provider_type in allowed if allowed else provider_type is None


def is_type(name: str) -> bool:
    return name in TYPES


def is_edge_type(name: str) -> bool:
    return name in EDGE_TYPES


def is_allowed(from_type: str, edge_type: str, to_type: str) -> bool:
    return (from_type, edge_type, to_type) in TRIPLES


def describe() -> dict:
    order = list(EDGE_TYPES)
    return {
        "providers": {
            name: {"description": desc, "types": PROVIDER_TYPES[name]}
            for name, desc in PROVIDERS.items()
        },
        "fields": FIELDS,
        "types": TYPES,
        "edge_types": EDGE_TYPES,
        "triples": [
            {"from": f, "edge": e, "to": t}
            for f, e, t in sorted(TRIPLES, key=lambda x: (order.index(x[1]), x[0], x[2]))
        ],
    }
