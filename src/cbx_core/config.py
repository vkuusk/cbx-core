"""Runtime configuration from CBX_* environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    host: str
    port: int
    webui_dir: Path


def _default_webui_dir() -> Path:
    # src/cbx_core/config.py -> repo root / webui
    return Path(__file__).resolve().parents[2] / "webui"


def load(env: dict[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    return Config(
        neo4j_uri=env.get("CBX_NEO4J_URI", "bolt://127.0.0.1:27687"),
        neo4j_user=env.get("CBX_NEO4J_USER", "neo4j"),
        neo4j_password=env.get("CBX_NEO4J_PASSWORD", "cbx-dev-password"),
        host=env.get("CBX_HOST", "127.0.0.1"),
        port=int(env.get("CBX_PORT", "2727")),
        webui_dir=Path(env.get("CBX_WEBUI_DIR", str(_default_webui_dir()))),
    )
