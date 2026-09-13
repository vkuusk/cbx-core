"""Tests run against a real Neo4j and wipe every Resource node before each test."""

import os
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from cbx_core import config
from cbx_core.main import create_app

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@pytest.fixture(scope="session")
def cfg() -> config.Config:
    c = config.load()
    host = urlparse(c.neo4j_uri).hostname
    if host not in LOCAL_HOSTS and not os.environ.get("CBX_TEST_ALLOW_REMOTE"):
        pytest.exit(f"refusing to run tests against non-local Neo4j {c.neo4j_uri}", returncode=2)
    return c


@pytest.fixture(scope="session")
def client(cfg):
    with TestClient(create_app(cfg)) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db(client):
    client.portal.call(client.app.state.repo.wipe)
