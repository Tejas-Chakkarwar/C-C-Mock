from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    uri: str
    user: str
    password: str


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    values = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USER": os.getenv("NEO4J_USER"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise ValueError(
            "required Neo4j settings are missing: "
            + ", ".join(missing)
            + "; copy .env.example to .env and set them"
        )
    try:
        parsed_uri = urlparse(values["NEO4J_URI"])
    except ValueError as exc:
        raise ValueError(f"invalid NEO4J_URI: {exc}") from exc
    if parsed_uri.scheme not in {"bolt", "bolt+s", "neo4j", "neo4j+s"}:
        raise ValueError("NEO4J_URI must use a Neo4j Bolt/neo4j URI scheme")
    if parsed_uri.hostname is None:
        raise ValueError("NEO4J_URI must include a host")
    if parsed_uri.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("NEO4J_URI must point to localhost for this local project")
    return Settings(
        uri=values["NEO4J_URI"],
        user=values["NEO4J_USER"],
        password=values["NEO4J_PASSWORD"],
    )

