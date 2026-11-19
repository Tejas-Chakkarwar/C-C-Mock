from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ConstraintError, Neo4jError, ServiceUnavailable

from .config import Settings
from .errors import DataIntegrityError, DatabaseUnavailableError, QueryError


@dataclass(frozen=True)
class LoggedQuery:
    name: str
    query: str
    params: dict[str, Any]
    rows: int


class QueryLog:
    def __init__(self) -> None:
        self._entries: list[LoggedQuery] = []
        self.action: str | None = None

    def begin_action(self, label: str) -> None:
        self.action = label
        self._entries.clear()

    def record(self, entry: LoggedQuery) -> None:
        self._entries.append(entry)

    def entries(self) -> list[LoggedQuery]:
        return list(self._entries)


def _redact(value: Any, key: str | None = None) -> Any:
    if key and "password" in key.lower():
        return "***"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 20:
            return f"[... {len(value)} items]"
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return [_redact(item) for item in value]
    return value


class Database:
    def __init__(self, settings: Settings, query_log: QueryLog | None = None) -> None:
        self.query_log = query_log or QueryLog()
        try:
            self.driver = GraphDatabase.driver(
                settings.uri,
                auth=(settings.user, settings.password),
            )
            self.driver.verify_connectivity()
        except (AuthError, ServiceUnavailable, OSError) as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def close(self) -> None:
        self.driver.close()

    def _run(self, query_name: str, query: str, *, log: bool, **params: Any):
        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                records = [record.data() for record in result]
                summary = result.consume()
        except ConstraintError as exc:
            raise DataIntegrityError(str(exc)) from exc
        except (Neo4jError, OSError) as exc:
            raise QueryError(str(exc)) from exc
        if log:
            self.query_log.record(
                LoggedQuery(query_name, query, _redact(params), len(records))
            )
        return records, summary

    def read(self, query_name: str, query: str, **params: Any):
        return self._run(query_name, query, log=True, **params)

    def write(self, query_name: str, query: str, *, log: bool = True, **params: Any):
        return self._run(query_name, query, log=log, **params)

