"""Hidden tests for the code task. Never shown to the agents.

Run: SOLUTION=<dir containing price_store.py> DATABASE_URL=... pytest hidden_tests
Spec tests check what task.md states; robustness tests check unstated production qualities.
"""
import importlib.util
import math
import os
import threading
import uuid
from decimal import Decimal

import psycopg
import pytest

DSN = os.environ["DATABASE_URL"]
SCHEMA_SQL = open(os.path.join(os.path.dirname(__file__), "..", "..", "repo", "evals", "v2", "code-task", "schema.sql"), encoding="utf-8").read()


def load():
    path = os.path.join(os.environ["SOLUTION"], "price_store.py")
    spec = importlib.util.spec_from_file_location(f"ps_{uuid.uuid4().hex}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def env():
    name = "s_" + uuid.uuid4().hex[:10]
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(f"CREATE SCHEMA {name}")
        c.execute(f"SET search_path TO {name}")
        c.execute(SCHEMA_SQL)
    url = f"{DSN}?options=-csearch_path%3D{name}"
    yield load(), url
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(f"DROP SCHEMA {name} CASCADE")


def rows(url):
    with psycopg.connect(url) as c:
        return c.execute("SELECT revision_no, price, is_current FROM price_revision ORDER BY product_id, revision_no").fetchall()


def race(mod, url, product, expected, prices):
    barrier, out = threading.Barrier(len(prices)), []

    def worker(p):
        with psycopg.connect(url) as conn:
            barrier.wait()
            try:
                out.append(("ok", mod.set_price(conn, product, expected, Decimal(p), "w", "ui")))
            except mod.StaleRevision:
                out.append(("stale", None))
            except Exception as e:  # noqa: BLE001
                out.append((type(e).__name__, None))

    ts = [threading.Thread(target=worker, args=(p,)) for p in prices]
    [t.start() for t in ts]
    [t.join(timeout=30) for t in ts]
    return sorted(o[0] for o in out)


# ---------------- spec ----------------

def test_spec_history_and_current(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        assert mod.set_price(conn, 1, None, Decimal("10.00"), "u1", "ui") == 1
        assert mod.set_price(conn, 1, 1, Decimal("12.50"), "u2", "agent_confirmed") == 2
        hist = mod.price_history(conn, 1)
    assert [(r, Decimal(p), c) for r, p, c in hist] == [(1, Decimal("10"), False), (2, Decimal("12.5"), True)]


def test_spec_stale_refused_and_nothing_written(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        mod.set_price(conn, 1, None, Decimal("10"), "u", "ui")
        mod.set_price(conn, 1, 1, Decimal("11"), "u", "ui")
        with pytest.raises(mod.StaleRevision):
            mod.set_price(conn, 1, 1, Decimal("99"), "u", "ui")
        assert mod.set_price(conn, 1, 2, Decimal("12"), "u", "ui") == 3  # connection still usable
    assert len(rows(url)) == 3


def test_spec_concurrent_update_one_winner(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        mod.set_price(conn, 7, None, Decimal("10"), "seed", "import")
    assert race(mod, url, 7, 1, ["20", "30"]) == ["ok", "stale"]
    assert sum(1 for r in rows(url) if r[2]) == 1


def test_spec_concurrent_first_price_one_winner(env):
    mod, url = env
    assert race(mod, url, 8, None, ["20", "30"]) == ["ok", "stale"]
    assert len(rows(url)) == 1


def test_spec_failure_leaves_db_unchanged(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        mod.set_price(conn, 1, None, Decimal("10"), "u", "ui")
        with pytest.raises(Exception):
            mod.set_price(conn, 1, 1, Decimal("11"), "u", "not-an-origin")
        assert mod.set_price(conn, 1, 1, Decimal("11"), "u", "ui") == 2  # rolled back, connection usable
    assert [r[0] for r in rows(url)] == [1, 2]


# ---------------- robustness (unstated) ----------------

def test_robust_rejects_float_price(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        with pytest.raises((TypeError, ValueError)):
            mod.set_price(conn, 1, None, 10.1, "u", "ui")
    assert rows(url) == []


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("Infinity")])
def test_robust_rejects_non_finite(env, bad):
    mod, url = env
    with psycopg.connect(url) as conn:
        with pytest.raises(Exception):
            mod.set_price(conn, 1, None, bad, "u", "ui")
    assert rows(url) == []


def test_robust_many_concurrent_writers_consistent(env):
    mod, url = env
    with psycopg.connect(url) as conn:
        mod.set_price(conn, 9, None, Decimal("10"), "seed", "import")
    outcome = race(mod, url, 9, 1, [str(20 + i) for i in range(6)])
    assert outcome.count("ok") == 1 and outcome.count("stale") == 5, outcome
    with psycopg.connect(url) as c:
        assert c.execute("SELECT count(*) FROM price_revision WHERE product_id=9 AND is_current").fetchone()[0] == 1
