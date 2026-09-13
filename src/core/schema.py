"""Graph schema: providers, node types with normalized attributes, edge types, allowed triples.

The single source of truth for what the core can hold. Served as-is by GET /api/schema.
"""

# provider -> what native_id holds
PROVIDERS: dict[str, str] = {
    "on-prem": "inventory tag (the sticker on the device)",
    "aws": "resource id or ARN",
    "gcp": "resource self-link or id",
}

# type -> meaning and normalized attribute names (values live in Node.attrs)
TYPES: dict[str, dict] = {
    "Organization": {
        "description": "Root of the graph. No provider binding.",
        "attributes": [],
    },
    "Scope": {
        "description": "Administrative container: cloud account, project, or a physical site.",
        "attributes": ["environment"],
    },
    "Network": {
        "description": "Routed network: VPC, VNet, or a LAN / VLAN.",
        "attributes": ["cidr"],
    },
    "Subnet": {
        "description": "Address range inside a network.",
        "attributes": ["cidr", "availability_zone"],
    },
    "NetworkDevice": {
        "description": "Physical or virtual switch, router, or firewall.",
        "attributes": ["model", "management_ip"],
    },
    "ComputeNode": {
        "description": "VM, bare-metal host, or dedicated instance.",
        "attributes": ["instance_type", "state", "image", "private_ips", "public_ips"],
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


def is_type(name: str) -> bool:
    return name in TYPES


def is_edge_type(name: str) -> bool:
    return name in EDGE_TYPES


def is_allowed(from_type: str, edge_type: str, to_type: str) -> bool:
    return (from_type, edge_type, to_type) in TRIPLES


def describe() -> dict:
    order = list(EDGE_TYPES)
    return {
        "providers": {name: {"native_id": desc} for name, desc in PROVIDERS.items()},
        "types": TYPES,
        "edge_types": EDGE_TYPES,
        "triples": [
            {"from": f, "edge": e, "to": t}
            for f, e, t in sorted(TRIPLES, key=lambda x: (order.index(x[1]), x[0], x[2]))
        ],
    }
