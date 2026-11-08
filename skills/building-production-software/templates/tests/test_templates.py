"""Self-checks for the templates. Run: DATABASE_URL=postgresql://... pytest templates/tests

Each test creates and drops its own database objects, so point DATABASE_URL at a throwaway database.
"""
import os
import pathlib
import sys
import threading
import types
import uuid

import psycopg
import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
DSN = os.environ.get("DATABASE_URL")
needs_db = pytest.mark.skipif(not DSN, reason="DATABASE_URL not set")
sys.path.insert(0, str(HERE))
import migrate  # noqa: E402


@pytest.fixture
def schema():
    """A fresh schema per test, dropped afterwards."""
    name = "t_" + uuid.uuid4().hex[:10]
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(f"CREATE SCHEMA {name}")
    yield f"{DSN}{'&' if '?' in DSN else '?'}options=-csearch_path%3D{name}"
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(f"DROP SCHEMA {name} CASCADE")


# --- supersede.sql ------------------------------------------------------------------------

@needs_db
def test_supersede_keeps_history_and_one_current_row(schema):
    with psycopg.connect(schema, autocommit=True) as c:
        c.execute((HERE / "supersede.sql").read_text(encoding="utf-8"))
        assert c.execute("SELECT supersede_price(1, NULL, 10.00, 'u1', 'ui')").fetchone()[0] == 1
        assert c.execute("SELECT supersede_price(1, 1, 12.50, 'u2', 'agent_confirmed')").fetchone()[0] == 2
        rows = c.execute("SELECT revision_no, price, is_current FROM price_revision ORDER BY 1").fetchall()
        assert [(r, str(p), cur) for r, p, cur in rows] == [(1, "10.0000", False), (2, "12.5000", True)]


@needs_db
def test_supersede_refuses_a_stale_revision(schema):
    with psycopg.connect(schema, autocommit=True) as c:
        c.execute((HERE / "supersede.sql").read_text(encoding="utf-8"))
        c.execute("SELECT supersede_price(1, NULL, 10, 'u1', 'ui')")
        c.execute("SELECT supersede_price(1, 1, 11, 'u1', 'ui')")
        with pytest.raises(psycopg.Error) as err:
            c.execute("SELECT supersede_price(1, 1, 99, 'u2', 'ui')")  # caller saw revision 1, current is 2
        assert err.value.sqlstate == "SR409"
        assert c.execute("SELECT count(*) FROM price_revision").fetchone()[0] == 2


@needs_db
def test_supersede_race_two_connections_one_wins(schema):
    """Two writers that both saw revision 1: exactly one succeeds. Fails if the lock is removed."""
    with psycopg.connect(schema, autocommit=True) as c:
        c.execute((HERE / "supersede.sql").read_text(encoding="utf-8"))
        c.execute("SELECT supersede_price(7, NULL, 10, 'seed', 'import')")
    barrier, outcomes = threading.Barrier(2), []

    def writer(price):
        with psycopg.connect(schema) as conn:
            try:
                barrier.wait()
                conn.execute("SELECT supersede_price(7, 1, %s, 'w', 'ui')", (price,))
                conn.commit()
                outcomes.append("ok")
            except psycopg.Error as e:
                outcomes.append(e.sqlstate)

    threads = [threading.Thread(target=writer, args=(p,)) for p in (20, 30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == ["SR409", "ok"]
    with psycopg.connect(schema) as c:
        assert c.execute("SELECT count(*) FROM price_revision WHERE is_current").fetchone()[0] == 1


# --- migrate.py ---------------------------------------------------------------------------

@needs_db
def test_migrate_applies_once_and_refuses_edited_or_missing_files(schema, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", schema)
    (tmp_path / "0001_a.sql").write_text("CREATE TABLE a (id int);", encoding="utf-8")
    (tmp_path / "0002_b.sql").write_text("CREATE TABLE b (id int); INSERT INTO b VALUES (1);", encoding="utf-8")

    assert migrate.main(["--dir", str(tmp_path), "--dry-run"]) == 0
    assert "would apply 0001_a.sql" in capsys.readouterr().out
    assert migrate.main(["--dir", str(tmp_path)]) == 0
    assert migrate.main(["--dir", str(tmp_path)]) == 0          # second run is a no-op
    assert "up to date" in capsys.readouterr().out

    (tmp_path / "0001_a.sql").write_text("CREATE TABLE a (id int); -- edited", encoding="utf-8")
    assert migrate.main(["--dir", str(tmp_path)]) == 2          # edited applied file -> refused
    (tmp_path / "0001_a.sql").write_text("CREATE TABLE a (id int);", encoding="utf-8")
    (tmp_path / "0002_b.sql").unlink()
    assert migrate.main(["--dir", str(tmp_path)]) == 2          # missing applied file -> refused


@needs_db
def test_migrate_rolls_back_a_failing_file(schema, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", schema)
    (tmp_path / "0001_bad.sql").write_text("CREATE TABLE c (id int); SELECT 1/0;", encoding="utf-8")
    with pytest.raises(psycopg.Error):
        migrate.main(["--dir", str(tmp_path)])
    with psycopg.connect(schema) as c:
        assert c.execute("SELECT to_regclass('c')").fetchone()[0] is None
        assert c.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 0


# --- test_route_auth.py -------------------------------------------------------------------

def _run_route_auth_template(app, monkeypatch):
    """Load the template against a given app and return its failing (method, path) pairs."""
    fastapi = pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    fake = types.ModuleType("myapp.main")
    fake.app = app
    monkeypatch.setitem(sys.modules, "myapp", types.ModuleType("myapp"))
    monkeypatch.setitem(sys.modules, "myapp.main", fake)
    ns: dict = {}
    exec(compile((HERE / "test_route_auth.py").read_text(encoding="utf-8"), "test_route_auth.py", "exec"), ns)
    failures = []
    for method, path in [r for r in ns["ROUTES"] if r not in ns["PUBLIC"]]:
        try:
            ns["test_route_refuses_anonymous"](method, path)
        except AssertionError:
            failures.append((method, path))
    ns["test_route_discovery_found_protected_routes"]()
    ns["test_public_list_has_no_stale_entries"]()
    return failures, fastapi


def _app(protect_items: bool):
    from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException

    def user(authorization: str | None = Header(None)):
        if authorization != "Bearer ok":
            raise HTTPException(401)

    app = FastAPI()
    app.get("/health")(lambda: {"ok": True})
    secured = APIRouter(dependencies=[Depends(user)])
    secured.post("/orders")(lambda: {})
    secured.patch("/orders/{order_id}")(lambda order_id: {})
    app.include_router(secured)
    items = APIRouter(dependencies=[Depends(user)] if protect_items else [])
    items.delete("/items/{item_id}")(lambda item_id: {})
    app.include_router(items)
    return app


def test_route_auth_template_passes_when_every_route_is_protected(monkeypatch):
    pytest.importorskip("fastapi")
    failures, _ = _run_route_auth_template(_app(protect_items=True), monkeypatch)
    assert failures == []


def test_route_auth_template_catches_an_unprotected_route(monkeypatch):
    pytest.importorskip("fastapi")
    failures, _ = _run_route_auth_template(_app(protect_items=False), monkeypatch)
    assert failures == [("DELETE", "/items/{item_id}")]
