"""REST API: schema, nodes, edges, traversal."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request, status

from . import schema
from .models import Edge, EdgeCreate, Graph, Node, NodeCreate, NodeEdges, NodeUpdate
from .repository import Conflict, NotFound, Repository

router = APIRouter(prefix="/api")


def repo(request: Request) -> Repository:
    return request.app.state.repo


def not_found(e: NotFound) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/health", tags=["health"])
async def health(request: Request):
    info = await request.app.state.driver.get_server_info()
    return {"status": "ok", "neo4j": info.agent}


@router.get("/schema", tags=["schema"])
async def get_schema():
    return schema.describe()


@router.get("/nodes", response_model=list[Node], tags=["nodes"])
async def list_nodes(request: Request, type: str | None = None, provider: str | None = None):
    return await repo(request).list_nodes(type=type, provider=provider)


@router.post("/nodes", response_model=Node, status_code=status.HTTP_201_CREATED, tags=["nodes"])
async def create_node(request: Request, data: NodeCreate):
    if not schema.is_type(data.type):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown type {data.type}")
    if not schema.is_provider(data.provider):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown provider {data.provider}")
    if not schema.has_binding(data.type) and (data.provider or data.provider_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{data.type} has no provider binding")
    if data.type == "Scope" and not data.provider:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Scope requires a provider")
    check_provider_type(data.provider, data.type, data.provider_type)
    try:
        return await repo(request).create_node(data)
    except Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e


def check_provider_type(provider: str | None, type: str, provider_type: str | None) -> None:
    if not schema.is_provider_type(provider, type, provider_type):
        allowed = schema.provider_types(provider, type) or ["none"]
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"provider_type for {provider} {type} must be one of {allowed}",
        )


@router.get("/nodes/{id}", response_model=Node, tags=["nodes"])
async def get_node(request: Request, id: str):
    try:
        return await repo(request).get_node(id)
    except NotFound as e:
        raise not_found(e) from e


@router.patch("/nodes/{id}", response_model=Node, tags=["nodes"])
async def update_node(request: Request, id: str, patch: NodeUpdate):
    try:
        if "provider_type" in patch.model_fields_set:
            current = await repo(request).get_node(id)
            check_provider_type(current.provider, current.type, patch.provider_type)
        return await repo(request).update_node(id, patch)
    except NotFound as e:
        raise not_found(e) from e
    except Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e


@router.delete("/nodes/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["nodes"])
async def delete_node(request: Request, id: str):
    try:
        await repo(request).delete_node(id)
    except NotFound as e:
        raise not_found(e) from e


@router.get(
    "/nodes/{id}/edges", response_model=NodeEdges, response_model_by_alias=True, tags=["nodes"]
)
async def node_edges(request: Request, id: str):
    try:
        out, inc = await repo(request).node_edges(id)
    except NotFound as e:
        raise not_found(e) from e
    return NodeEdges(out=out, **{"in": inc})


@router.get("/nodes/{id}/traverse", response_model=Graph, tags=["nodes"])
async def traverse(
    request: Request,
    id: str,
    edge_types: str = Query(default=",".join(schema.EDGE_TYPES)),
    direction: Literal["out", "in", "both"] = "out",
    depth: int = Query(default=5, ge=1, le=20),
):
    types = [t for t in edge_types.split(",") if t]
    bad = [t for t in types if not schema.is_edge_type(t)]
    if bad:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown edge types {bad}")
    try:
        nodes, edges = await repo(request).traverse(id, types, direction, depth)
    except NotFound as e:
        raise not_found(e) from e
    return Graph(nodes=nodes, edges=edges)


@router.get("/edges", response_model=list[Edge], tags=["edges"])
async def list_edges(request: Request, type: str | None = None):
    return await repo(request).list_edges(type=type)


@router.post("/edges", response_model=Edge, status_code=status.HTTP_201_CREATED, tags=["edges"])
async def create_edge(request: Request, data: EdgeCreate):
    if not schema.is_edge_type(data.type):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown edge type {data.type}")
    r = repo(request)
    try:
        a, b = await r.get_node(data.from_id), await r.get_node(data.to_id)
    except NotFound as e:
        raise not_found(e) from e
    if not schema.is_allowed(a.type, data.type, b.type):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"{a.type} -{data.type}-> {b.type} is not allowed"
        )
    return await r.create_edge(data)


@router.get("/edges/{id}", response_model=Edge, tags=["edges"])
async def get_edge(request: Request, id: str):
    try:
        return await repo(request).get_edge(id)
    except NotFound as e:
        raise not_found(e) from e


@router.delete("/edges/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["edges"])
async def delete_edge(request: Request, id: str):
    try:
        await repo(request).delete_edge(id)
    except NotFound as e:
        raise not_found(e) from e
