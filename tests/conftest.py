"""Tests run against the separate test Neo4j (compose service neo4j-test) and wipe every
Resource node in it before each test."""

import os
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from core import config
from core.main import create_app

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@pytest.fixture(scope="session")
def cfg() -> config.Config:
    env = os.environ
    c = config.load(
        {
            **env,
            "CBX_NEO4J_URI": env.get("CBX_TEST_NEO4J_URI", "bolt://127.0.0.1:27688"),
            "CBX_NEO4J_PASSWORD": env.get("CBX_TEST_NEO4J_PASSWORD", "cbx-test-password"),
        }
    )
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
