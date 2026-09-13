"""Graph schema: node types, their normalized attributes, edge types, allowed triples."""

# type -> normalized attribute names (values live in Node.attrs)
TYPES: dict[str, list[str]] = {
    "Organization": [],
    "Scope": ["environment"],
    "Network": ["cidr"],
    "Subnet": ["cidr", "availability_zone"],
    "ComputeNode": ["instance_type", "state", "image", "private_ips", "public_ips"],
}

EDGE_TYPES: list[str] = ["CONTAINS", "RUNS_IN"]

# (from type, edge type, to type)
TRIPLES: set[tuple[str, str, str]] = {
    ("Organization", "CONTAINS", "Scope"),
    ("Scope", "CONTAINS", "Network"),
    ("Network", "CONTAINS", "Subnet"),
    ("ComputeNode", "RUNS_IN", "Subnet"),
}


def is_type(name: str) -> bool:
    return name in TYPES


def is_edge_type(name: str) -> bool:
    return name in EDGE_TYPES


def is_allowed(from_type: str, edge_type: str, to_type: str) -> bool:
    return (from_type, edge_type, to_type) in TRIPLES


def describe() -> dict:
    return {
        "types": {name: {"attributes": attrs} for name, attrs in TYPES.items()},
        "edge_types": list(EDGE_TYPES),
        "triples": [
            {"from": f, "edge": e, "to": t}
            for f, e, t in sorted(TRIPLES, key=lambda x: (EDGE_TYPES.index(x[1]), x[0], x[2]))
        ],
    }
