def node(client, type, name, **kw):
    r = client.post("/api/nodes", json={"type": type, "name": name, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def edge(client, type, from_id, to_id):
    r = client.post("/api/edges", json={"type": type, "from_id": from_id, "to_id": to_id})
    assert r.status_code == 201, r.text
    return r.json()


def aws_tree(client):
    org = node(client, "Organization", "acme")
    acct = node(client, "Scope", "prod", provider="aws", native_id="123456789012")
    vpc = node(
        client,
        "Network",
        "vpc-main",
        provider="aws",
        native_id="vpc-1",
        attrs={"cidr": "10.0.0.0/16"},
    )
    sub = node(client, "Subnet", "sub-a", provider="aws", native_id="subnet-1", region="us-east-1")
    ec2 = node(
        client, "ComputeNode", "web-1", provider="aws", native_id="i-1", tags={"role": "web"}
    )
    edge(client, "CONTAINS", org["id"], acct["id"])
    edge(client, "CONTAINS", acct["id"], vpc["id"])
    edge(client, "CONTAINS", vpc["id"], sub["id"])
    edge(client, "RUNS_IN", ec2["id"], sub["id"])
    return org, acct, vpc, sub, ec2


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_schema(client):
    s = client.get("/api/schema").json()
    assert set(s["providers"]) == {"on-prem", "aws", "gcp"}
    assert s["types"]["ComputeNode"]["attributes"]
    assert set(s["edge_types"]) == {"CONTAINS", "RUNS_IN", "SERVED_BY"}
    assert {"from": "ComputeNode", "edge": "RUNS_IN", "to": "Subnet"} in s["triples"]


def test_unknown_provider_rejected(client):
    r = client.post("/api/nodes", json={"type": "ComputeNode", "name": "x", "provider": "azure"})
    assert r.status_code == 400


def test_manual_edits_carry_inventory_source(client):
    n = node(client, "ComputeNode", "nas", provider="on-prem", native_id="INV-0042")
    assert [s["importer"] for s in n["sources"]] == ["inventory"]
    assert n["sources"][0]["origin"] == "declared"
    first = n["sources"][0]["last_seen"]

    r = client.patch(f"/api/nodes/{n['id']}", json={"name": "nas-1"}).json()
    assert len(r["sources"]) == 1 and r["sources"][0]["last_seen"] >= first

    explicit = [{"importer": "aws", "origin": "observed", "first_seen": first, "last_seen": first}]
    n2 = node(client, "ComputeNode", "web", provider="aws", native_id="i-9", sources=explicit)
    assert [s["importer"] for s in n2["sources"]] == ["aws"]


def test_home_lab_tree(client):
    lan = node(client, "Network", "LAN", provider="on-prem", native_id="LAN-1")
    sw = node(client, "NetworkDevice", "switch-1", provider="on-prem", native_id="INV-0007")
    sub = node(
        client,
        "Subnet",
        "lab",
        provider="on-prem",
        native_id="INV-0007/10",
        attrs={"cidr": "10.0.0.0/24"},
    )
    edge(client, "CONTAINS", lan["id"], sw["id"])
    edge(client, "CONTAINS", lan["id"], sub["id"])
    edge(client, "SERVED_BY", sub["id"], sw["id"])
    e = client.get(f"/api/nodes/{sw['id']}/edges").json()
    assert {x["type"] for x in e["in"]} == {"CONTAINS", "SERVED_BY"}


def test_node_crud(client):
    n = node(
        client, "ComputeNode", "web-1", provider="aws", native_id="i-1", attrs={"state": "running"}
    )
    assert n["type"] == "ComputeNode" and n["attrs"] == {"state": "running"}

    assert client.get(f"/api/nodes/{n['id']}").json()["name"] == "web-1"

    r = client.patch(f"/api/nodes/{n['id']}", json={"name": "web-2", "tags": {"env": "prod"}})
    assert r.status_code == 200
    assert r.json()["name"] == "web-2" and r.json()["tags"] == {"env": "prod"}
    assert r.json()["attrs"] == {"state": "running"}

    assert [x["id"] for x in client.get("/api/nodes?type=ComputeNode").json()] == [n["id"]]
    assert client.get("/api/nodes?type=Network").json() == []

    assert client.delete(f"/api/nodes/{n['id']}").status_code == 204
    assert client.get(f"/api/nodes/{n['id']}").status_code == 404


def test_unknown_type_rejected(client):
    r = client.post("/api/nodes", json={"type": "Pod", "name": "x"})
    assert r.status_code == 400


def test_natural_key_unique(client):
    node(client, "ComputeNode", "a", provider="aws", native_id="i-1")
    r = client.post(
        "/api/nodes",
        json={"type": "ComputeNode", "name": "b", "provider": "aws", "native_id": "i-1"},
    )
    assert r.status_code == 409


def test_edge_rules(client):
    org = node(client, "Organization", "acme")
    ec2 = node(client, "ComputeNode", "web-1")
    r = client.post(
        "/api/edges", json={"type": "CONTAINS", "from_id": org["id"], "to_id": ec2["id"]}
    )
    assert r.status_code == 400
    r = client.post("/api/edges", json={"type": "HOSTS", "from_id": org["id"], "to_id": ec2["id"]})
    assert r.status_code == 400
    r = client.post(
        "/api/edges", json={"type": "CONTAINS", "from_id": org["id"], "to_id": "missing"}
    )
    assert r.status_code == 404


def test_edges_and_traverse(client):
    org, _, vpc, sub, ec2 = aws_tree(client)

    e = client.get(f"/api/nodes/{sub['id']}/edges").json()
    assert {x["from_id"] for x in e["in"]} == {vpc["id"], ec2["id"]}
    assert e["out"] == []

    g = client.get(f"/api/nodes/{org['id']}/traverse?edge_types=CONTAINS").json()
    assert {n["name"] for n in g["nodes"]} == {"acme", "prod", "vpc-main", "sub-a"}
    assert len(g["edges"]) == 3

    g = client.get(f"/api/nodes/{sub['id']}/traverse?direction=in&depth=1").json()
    assert {n["name"] for n in g["nodes"]} == {"sub-a", "vpc-main", "web-1"}

    g = client.get(f"/api/nodes/{ec2['id']}/traverse?direction=out").json()
    assert {n["name"] for n in g["nodes"]} == {"web-1", "sub-a"}

    leaf = client.get(f"/api/nodes/{sub['id']}/traverse?direction=out").json()
    assert leaf == {"nodes": [client.get(f"/api/nodes/{sub['id']}").json()], "edges": []}

    all_edges = client.get("/api/edges").json()
    assert len(all_edges) == 4
    eid = all_edges[0]["id"]
    assert client.get(f"/api/edges/{eid}").json()["id"] == eid
    assert client.delete(f"/api/edges/{eid}").status_code == 204
    assert client.get(f"/api/edges/{eid}").status_code == 404


def test_delete_node_removes_edges(client):
    org, acct, *_ = aws_tree(client)
    assert client.delete(f"/api/nodes/{acct['id']}").status_code == 204
    assert client.get(f"/api/nodes/{org['id']}/edges").json()["out"] == []
    assert len(client.get("/api/edges").json()) == 2
