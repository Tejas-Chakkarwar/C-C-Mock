from __future__ import annotations

import pytest

import cyphercircle.config as config
from cyphercircle.db import LoggedQuery, QueryLog, _redact


def _without_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda *_args, **_kwargs: False)
    for name in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
        monkeypatch.delenv(name, raising=False)


def test_missing_neo4j_settings_are_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    _without_dotenv(monkeypatch)

    with pytest.raises(ValueError, match="NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"):
        config.load_settings()


@pytest.mark.parametrize(
    ("uri", "message"),
    [
        ("http://localhost:7687", "Bolt/neo4j URI scheme"),
        ("bolt://example.com:7687", "localhost"),
        ("bolt://", "include a host"),
    ],
)
def test_invalid_neo4j_uri_is_rejected(
    monkeypatch: pytest.MonkeyPatch, uri: str, message: str
) -> None:
    _without_dotenv(monkeypatch)
    monkeypatch.setenv("NEO4J_URI", uri)
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")

    with pytest.raises(ValueError, match=message):
        config.load_settings()


def test_query_log_records_and_redacts_nested_passwords() -> None:
    log = QueryLog()
    log.begin_action("TEST")
    log.record(
        LoggedQuery(
            "EXAMPLE",
            "RETURN 1",
            _redact({"rows": [{"password_hash": "secret", "name": "Alice"}]}),
            1,
        )
    )

    entry = log.entries()[0]
    assert entry.params == {"rows": [{"password_hash": "***", "name": "Alice"}]}
    log.begin_action("NEXT")
    assert log.entries() == []
