from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from cyphercircle.config import WebSettings
from cyphercircle.errors import AuthenticationError, QueryError, ValidationError
from cyphercircle.models import (
    CircleSummary,
    Connection,
    ConnectionCounts,
    GraphStats,
    MutualConnections,
    Profile,
    Recommendation,
    RelationshipStatus,
    SearchResult,
    Session,
    UserSummary,
)
from cyphercircle.web import WebServices, create_app


NOW = datetime(2024, 1, 1, tzinfo=UTC)


def _profile(username: str = "alice.a", name: str = "Alice") -> Profile:
    return Profile(
        username,
        name,
        f"{username}@example.com",
        "A short bio",
        "Toronto",
        ["Designers"],
        1,
        NOW,
        4,
        7,
    )


class FakeAuth:
    def __init__(self) -> None:
        self.login_calls: list[tuple[str, str]] = []
        self.register_calls: list[tuple] = []
        self.login_error: Exception | None = None
        self.register_error: Exception | None = None

    def login(self, username: str, password: str) -> Session:
        self.login_calls.append((username, password))
        if self.login_error:
            raise self.login_error
        return Session("alice.a", "Alice")

    def register(self, *args, **kwargs) -> Session:
        self.register_calls.append((args, kwargs))
        if self.register_error:
            raise self.register_error
        return Session("alice.a", "Alice")


class FakeProfile:
    def __init__(self) -> None:
        self.profile = _profile()
        self.public_profile = _profile("bob.b", "Bob")
        self.circles = [CircleSummary("1:0", "Designers", 12), CircleSummary("2:0", "Builders", 8)]
        self.update_calls: list[dict] = []
        self.join_calls: list[str] = []
        self.leave_calls: list[str] = []

    def get_top_circles(self, limit: int = 10):
        return self.circles[:limit]

    def get_profile(self, _session: Session) -> Profile:
        return self.profile

    def get_public_profile(self, username: str) -> Profile:
        if username.lower() == "bob.b":
            return self.public_profile
        return _profile(username, "Someone")

    def update_profile(self, _session: Session, **kwargs) -> Profile:
        self.update_calls.append(kwargs)
        self.profile = _profile(name=kwargs.get("name") or "Alice")
        return self.profile

    def get_my_circles(self, _session: Session):
        return self.circles[:1]

    def join_circle(self, _session: Session, circle_id: str) -> bool:
        self.join_calls.append(circle_id)
        return True

    def leave_circle(self, _session: Session, circle_id: str) -> bool:
        self.leave_calls.append(circle_id)
        return True


class FakeGraph:
    def __init__(self) -> None:
        self.follow_calls: list[str] = []
        self.unfollow_calls: list[str] = []
        self.recommendation = Recommendation(
            UserSummary("bob.b", "Bob", "Toronto", 6),
            2,
            ["mid.one"],
            "network",
            None,
        )

    def recommendations(self, _session: Session, *, limit: int = 10):
        return [self.recommendation][:limit]

    def mutual_connections(self, _session: Session, _other: str, **_kwargs):
        return MutualConnections(1, [], RelationshipStatus(True, False))

    def connection_counts(self, _session: Session):
        return ConnectionCounts(4, 7)

    def following(self, _session: Session, *, skip: int, limit: int):
        return [Connection("bob.b", "Bob", "Toronto", NOW, True)][skip : skip + limit]

    def followers(self, _session: Session, *, skip: int, limit: int):
        return [Connection("bob.b", "Bob", "Toronto", NOW, True)][skip : skip + limit]

    def follow(self, _session: Session, target: str) -> bool:
        self.follow_calls.append(target)
        return True

    def unfollow(self, _session: Session, target: str) -> bool:
        self.unfollow_calls.append(target)
        return True


class FakeSearch:
    def search_users(self, _session: Session, _query: str, limit: int = 10):
        return [SearchResult("bob.b", "Bob", "Toronto", 6, False)][:limit]

    def popular_users(self, *, exclude=(), limit: int = 10):
        return [UserSummary("bob.b", "Bob", "Toronto", 6)][:limit]


class FakeStartup:
    def current_stats(self):
        return GraphStats(100, 240, 12)


class FakeVisualization:
    def __init__(self, tmp_path: Path) -> None:
        self.output_dir = tmp_path
        self.path = tmp_path / "network_alice.a.html"

    def generate(self, _session: Session):
        self.path.write_text("<!doctype html><title>Offline graph</title>", encoding="utf-8")
        return self.path


def _app(tmp_path: Path):
    auth = FakeAuth()
    profile = FakeProfile()
    graph = FakeGraph()
    services = WebServices(
        auth=auth,
        profile=profile,
        graph=graph,
        search=FakeSearch(),
        startup=FakeStartup(),
        visualization=FakeVisualization(tmp_path),
    )
    app = create_app(
        services,
        web_settings=WebSettings("127.0.0.1", 5000, "test-secret"),
        config={"TESTING": True},
    )
    return app, auth, profile, graph


def _csrf(client) -> str:
    with client.session_transaction() as state:
        return state["_csrf_token"]


def _login(client) -> None:
    client.get("/login")
    token = _csrf(client)
    response = client.post(
        "/login",
        data={"csrf_token": token, "username": "alice.a", "password": "password123"},
    )
    assert response.status_code == 302


def test_landing_page_shows_stats_and_primary_actions(tmp_path: Path) -> None:
    app, *_ = _app(tmp_path)
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"Cypher Circle" in response.data
    assert b"100" in response.data and b"240" in response.data
    assert b"Create your account" in response.data


def test_registration_success_stores_only_minimum_identity(tmp_path: Path) -> None:
    app, auth, *_ = _app(tmp_path)
    client = app.test_client()
    client.get("/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": _csrf(client),
            "name": "New Person",
            "email": "new@example.com",
            "username": "new.person",
            "password": "password123",
            "password_confirm": "password123",
            "bio": "Hello",
            "circle_ids": "1:0",
        },
    )
    assert response.status_code == 302
    assert auth.register_calls
    with client.session_transaction() as state:
        assert state["identity"] == {"username": "alice.a", "name": "Alice"}
        assert "password" not in str(dict(state))
        assert state["_csrf_token"]


def test_registration_error_never_repopulates_password(tmp_path: Path) -> None:
    app, auth, *_ = _app(tmp_path)
    auth.register_error = ValidationError("username is invalid")
    client = app.test_client()
    client.get("/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": _csrf(client),
            "name": "New Person",
            "email": "new@example.com",
            "username": "bad",
            "password": "password123",
            "password_confirm": "password123",
        },
    )
    assert response.status_code == 400
    assert b"username is invalid" in response.data
    assert b"password123" not in response.data


def test_registration_requires_matching_password_confirmation(tmp_path: Path) -> None:
    app, auth, *_ = _app(tmp_path)
    client = app.test_client()
    client.get("/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": _csrf(client),
            "name": "New Person",
            "email": "new@example.com",
            "username": "new.person",
            "password": "password123",
            "password_confirm": "different123",
        },
    )
    assert response.status_code == 400
    assert b"Passwords do not match" in response.data
    assert auth.register_calls == []
    assert b"password123" not in response.data


def test_login_failure_is_generic_and_password_is_not_rendered(tmp_path: Path) -> None:
    app, auth, *_ = _app(tmp_path)
    auth.login_error = AuthenticationError("Invalid username or password")
    client = app.test_client()
    client.get("/login")
    response = client.post(
        "/login",
        data={"csrf_token": _csrf(client), "username": "alice.a", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    assert b"wrong-password" not in response.data


def test_unauthorized_routes_redirect_and_csrf_is_required(tmp_path: Path) -> None:
    app, *_ = _app(tmp_path)
    client = app.test_client()
    response = client.get("/dashboard")
    assert response.status_code == 302 and "/login" in response.location
    response = client.post("/login", data={"username": "alice.a", "password": "password123"})
    assert response.status_code == 400
    assert b"Invalid or missing request token" in response.data


def test_authenticated_actions_render_and_use_services(tmp_path: Path) -> None:
    app, _auth, profile, graph = _app(tmp_path)
    client = app.test_client()
    _login(client)
    assert b"People worth knowing" in client.get("/dashboard").data
    assert b"Bob" in client.get("/users/bob.b").data
    assert b"Connections" in client.get("/connections").data
    assert b"Mutual connections" in client.get("/mutual?username=bob.b").data
    assert b"Bob" in client.get("/recommendations").data
    assert b"Bob" in client.get("/search?q=bo").data
    assert b"Popular users" in client.get("/popular").data
    assert b"Your circles" in client.get("/circles").data
    assert b"Network visualization" in client.get("/visualization").data

    token = _csrf(client)
    client.post("/users/bob.b/follow", data={"csrf_token": token, "next": "/dashboard"})
    client.post("/users/bob.b/unfollow", data={"csrf_token": token, "next": "/dashboard"})
    client.post("/circles/join", data={"csrf_token": token, "circle_id": "2:0"})
    client.post("/circles/leave", data={"csrf_token": token, "circle_id": "1:0"})
    client.post("/profile/edit", data={"csrf_token": token, "name": "Alice Updated", "bio": "-", "location": "-"})
    assert graph.follow_calls == ["bob.b"]
    assert graph.unfollow_calls == ["bob.b"]
    assert profile.join_calls == ["2:0"]
    assert profile.leave_calls == ["1:0"]
    assert profile.update_calls[0]["bio"] == "-"


def test_logout_clears_session_and_visualization_is_safely_embedded(tmp_path: Path) -> None:
    app, *_ = _app(tmp_path)
    client = app.test_client()
    _login(client)
    assert client.get("/visualization").status_code == 200
    response = client.get("/visualization/document")
    assert response.status_code == 200
    assert b"Offline graph" in response.data
    response = client.post("/logout", data={"csrf_token": _csrf(client)})
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_database_errors_are_sanitized(tmp_path: Path) -> None:
    app, _auth, profile, _graph = _app(tmp_path)
    profile.get_profile = lambda _session: (_ for _ in ()).throw(QueryError("neo4j password=secret"))  # type: ignore[method-assign]
    client = app.test_client()
    _login(client)
    response = client.get("/dashboard")
    assert response.status_code == 400
    assert b"database operation could not be completed" in response.data
    assert b"neo4j password=secret" not in response.data
    assert b"Traceback" not in response.data


def test_user_content_is_escaped_and_external_redirects_are_rejected(tmp_path: Path) -> None:
    app, _auth, profile, graph = _app(tmp_path)
    profile.profile = _profile(name="<script>alert(1)</script>")
    client = app.test_client()
    _login(client)
    response = client.get("/profile", follow_redirects=True)
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data

    token = _csrf(client)
    response = client.post(
        "/users/bob.b/follow",
        data={"csrf_token": token, "next": "https://evil.example/steal"},
    )
    assert response.status_code == 302
    assert response.location.endswith("/users/bob.b")
    assert graph.follow_calls == ["bob.b"]


def test_make_run_remains_the_cli_entry_point() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    assert "run:" in makefile
    assert "$(PYTHON) -m cyphercircle\n" in makefile
    assert "web:" in makefile
    assert "$(PYTHON) -m cyphercircle.web" in makefile
