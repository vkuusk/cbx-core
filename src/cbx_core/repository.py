"""Cypher queries over the Resource graph. Every node carries labels :Resource:<type>."""

import json
import uuid
from datetime import UTC, datetime

from neo4j import AsyncDriver
from neo4j.exceptions import ConstraintError

from .models import Edge, EdgeCreate, Node, NodeCreate, NodeUpdate

JSON_FIELDS = ("attrs", "native", "tags", "sources")


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _natural_key(provider: str | None, native_id: str | None) -> str | None:
    return f"{provider}:{native_id}" if provider and native_id else None


def _to_props(data: dict) -> dict:
    props = dict(data)
    for f in JSON_FIELDS:
        if f in props:
            props[f] = json.dumps(props[f], default=str)
    return props


def _node(props: dict) -> Node:
    data = dict(props)
    data.pop("natural_key", None)
    for f in JSON_FIELDS:
        data[f] = json.loads(data.get(f) or ("[]" if f == "sources" else "{}"))
    return Node(**data)


def _edge(row: dict) -> Edge:
    props = dict(row["props"])
    props["attrs"] = json.loads(props.get("attrs") or "{}")
    return Edge(type=row["type"], from_id=row["from_id"], to_id=row["to_id"], **props)


EDGE_RETURN = (
    "properties(r) AS props, type(r) AS type, startNode(r).id AS from_id, endNode(r).id AS to_id"
)


class Repository:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def _run(self, query: str, **params):
        result = await self.driver.execute_query(query, params)
        return result.records

    async def ensure_constraints(self) -> None:
        await self._run(
            "CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (n:Resource) REQUIRE n.id IS UNIQUE"
        )
        await self._run(
            "CREATE CONSTRAINT resource_natural_key IF NOT EXISTS "
            "FOR (n:Resource) REQUIRE n.natural_key IS UNIQUE"
        )

    # nodes

    async def create_node(self, data: NodeCreate) -> Node:
        now = _now()
        props = _to_props(data.model_dump(mode="json"))
        props.update(
            id=str(uuid.uuid4()),
            natural_key=_natural_key(data.provider, data.native_id),
            created_at=now,
            updated_at=now,
        )
        try:
            records = await self._run(
                f"CREATE (n:Resource:{data.type} $props) RETURN properties(n) AS n", props=props
            )
        except ConstraintError as e:
            raise Conflict(f"node with natural key {props['natural_key']} exists") from e
        return _node(records[0]["n"])

    async def list_nodes(self, type: str | None = None, provider: str | None = None) -> list[Node]:
        records = await self._run(
            "MATCH (n:Resource) "
            "WHERE ($type IS NULL OR n.type = $type) "
            "AND ($provider IS NULL OR n.provider = $provider) "
            "RETURN properties(n) AS n ORDER BY n.type, n.name",
            type=type,
            provider=provider,
        )
        return [_node(r["n"]) for r in records]

    async def get_node(self, id: str) -> Node:
        records = await self._run("MATCH (n:Resource {id: $id}) RETURN properties(n) AS n", id=id)
        if not records:
            raise NotFound(f"node {id}")
        return _node(records[0]["n"])

    async def update_node(self, id: str, patch: NodeUpdate) -> Node:
        changes = patch.model_dump(mode="json", exclude_unset=True)
        current = await self.get_node(id)
        provider = current.provider
        native_id = changes.get("native_id", current.native_id)
        props = _to_props(changes)
        props.update(natural_key=_natural_key(provider, native_id), updated_at=_now())
        try:
            records = await self._run(
                "MATCH (n:Resource {id: $id}) SET n += $props RETURN properties(n) AS n",
                id=id,
                props=props,
            )
        except ConstraintError as e:
            raise Conflict(f"node with natural key {props['natural_key']} exists") from e
        return _node(records[0]["n"])

    async def delete_node(self, id: str) -> None:
        records = await self._run(
            "MATCH (n:Resource {id: $id}) DETACH DELETE n RETURN count(n) AS c", id=id
        )
        if records[0]["c"] == 0:
            raise NotFound(f"node {id}")

    # edges

    async def create_edge(self, data: EdgeCreate) -> Edge:
        now = _now()
        props = {
            "id": str(uuid.uuid4()),
            "attrs": json.dumps(data.attrs, default=str),
            "created_at": now,
            "updated_at": now,
        }
        records = await self._run(
            "MATCH (a:Resource {id: $from_id}), (b:Resource {id: $to_id}) "
            f"CREATE (a)-[r:{data.type} $props]->(b) RETURN {EDGE_RETURN}",
            from_id=data.from_id,
            to_id=data.to_id,
            props=props,
        )
        if not records:
            raise NotFound(f"node {data.from_id} or {data.to_id}")
        return _edge(records[0])

    async def list_edges(self, type: str | None = None) -> list[Edge]:
        records = await self._run(
            "MATCH (a:Resource)-[r]->(b:Resource) "
            f"WHERE $type IS NULL OR type(r) = $type RETURN {EDGE_RETURN}",
            type=type,
        )
        return [_edge(r) for r in records]

    async def get_edge(self, id: str) -> Edge:
        records = await self._run(
            f"MATCH (a:Resource)-[r {{id: $id}}]->(b:Resource) RETURN {EDGE_RETURN}", id=id
        )
        if not records:
            raise NotFound(f"edge {id}")
        return _edge(records[0])

    async def delete_edge(self, id: str) -> None:
        records = await self._run("MATCH ()-[r {id: $id}]->() DELETE r RETURN count(r) AS c", id=id)
        if records[0]["c"] == 0:
            raise NotFound(f"edge {id}")

    async def node_edges(self, id: str) -> tuple[list[Edge], list[Edge]]:
        await self.get_node(id)
        out = await self._run(
            f"MATCH (a:Resource {{id: $id}})-[r]->(b:Resource) RETURN {EDGE_RETURN}", id=id
        )
        inc = await self._run(
            f"MATCH (a:Resource)-[r]->(b:Resource {{id: $id}}) RETURN {EDGE_RETURN}", id=id
        )
        return [_edge(r) for r in out], [_edge(r) for r in inc]

    async def traverse(
        self, id: str, edge_types: list[str], direction: str, depth: int
    ) -> tuple[list[Node], list[Edge]]:
        start = await self.get_node(id)
        types = "|".join(edge_types)
        left, right = {"out": ("-", "->"), "in": ("<-", "-"), "both": ("-", "-")}[direction]
        records = await self._run(
            f"MATCH p = (s:Resource {{id: $id}}){left}[:{types}*1..{depth}]{right}() "
            "UNWIND nodes(p) AS n UNWIND relationships(p) AS r "
            "WITH collect(DISTINCT n) AS ns, collect(DISTINCT r) AS rs "
            "RETURN [n IN ns | properties(n)] AS nodes, "
            "[r IN rs | {props: properties(r), type: type(r), "
            "from_id: startNode(r).id, to_id: endNode(r).id}] AS edges",
            id=id,
        )
        row = records[0] if records else None
        if not row or not row["nodes"]:
            return [start], []
        return [_node(n) for n in row["nodes"]], [_edge(e) for e in row["edges"]]

    async def wipe(self) -> None:
        await self._run("MATCH (n:Resource) DETACH DELETE n")
