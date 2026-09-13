"""API request and response models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    importer: str
    origin: Literal["declared", "observed"]
    first_seen: datetime
    last_seen: datetime


class NodeCreate(BaseModel):
    type: str
    name: str
    provider: str | None = None
    provider_type: str | None = None
    provider_id: str | None = None
    region: str | None = None
    attrs: dict[str, Any] = Field(default_factory=dict)
    native: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)
    sources: list[Source] = Field(default_factory=list)


class NodeUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    provider_id: str | None = None
    region: str | None = None
    attrs: dict[str, Any] | None = None
    native: dict[str, Any] | None = None
    tags: dict[str, str] | None = None
    sources: list[Source] | None = None


class Node(NodeCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class EdgeCreate(BaseModel):
    type: str
    from_id: str
    to_id: str
    attrs: dict[str, Any] = Field(default_factory=dict)


class Edge(EdgeCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class NodeEdges(BaseModel):
    out: list[Edge]
    in_: list[Edge] = Field(alias="in")

    model_config = {"populate_by_name": True}


class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
