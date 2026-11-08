"""Architecture fitness test: every route refuses anonymous callers unless listed as public.

A new route fails CI until it is protected or deliberately added to PUBLIC.
Adapt the two marked lines. Requires: fastapi, httpx, pytest.

Routes are discovered from the OpenAPI schema, which covers routers added with
include_router on every FastAPI version (newer versions no longer flatten them into
app.routes). Routes declared with include_in_schema=False are NOT discovered: list them
in EXTRA so they are checked too.
"""
import re

import pytest
from fastapi.testclient import TestClient

from myapp.main import app  # <- change to your FastAPI app

PUBLIC = {("GET", "/health")}  # <- every deliberately public (method, path)
EXTRA: set[tuple[str, str]] = set()  # routes hidden from the schema that must still be checked

_HTTP = {"get", "post", "put", "patch", "delete"}
ROUTES = sorted(
    {(method.upper(), path) for path, ops in app.openapi()["paths"].items() for method in ops if method in _HTTP}
    | EXTRA
)


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path)  # fill path params with a dummy value


@pytest.mark.parametrize("method,path", [r for r in ROUTES if r not in PUBLIC])
def test_route_refuses_anonymous(method, path):
    response = TestClient(app).request(method, _concrete(path))
    assert response.status_code == 401, f"{method} {path} answered {response.status_code} without a token"


def test_route_discovery_found_protected_routes():
    """Guards the guard: if discovery breaks, this fails instead of the suite passing vacuously."""
    assert any(r not in PUBLIC for r in ROUTES), "no protected routes discovered - check how routes are collected"


def test_public_list_has_no_stale_entries():
    assert PUBLIC <= set(ROUTES), f"PUBLIC lists routes that no longer exist: {PUBLIC - set(ROUTES)}"
