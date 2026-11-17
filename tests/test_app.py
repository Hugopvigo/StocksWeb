import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db, main


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    db.init_db(c)
    db.upsert_asset(c, {"ticker": "aapl.us", "name": "Apple", "kind": "stock", "quantity": 10, "avg_buy": 200, "override_price": None})
    db.upsert_quote(c, "aapl.us", {"price": 229.87, "prev_close": 227.2, "change_pct": 1.18, "as_of": "2026-11-17", "error": None})
    db.replace_history(c, "aapl.us", [("2026-11-14", 227.2), ("2026-11-17", 229.87)])
    yield c
    c.close()


@pytest.fixture
def client(conn, monkeypatch):
    monkeypatch.setenv("ADMIN_USER", "hugo")
    monkeypatch.setenv("ADMIN_PASSWORD", "secreto-de-prueba")
    app = main.create_app(conn=conn, refresh_fn=lambda c: None)
    return TestClient(app)


AUTH = ("hugo", "secreto-de-prueba")
PRIVATE_KEYS = {"quantity", "avg_buy", "override_price", "cost", "value", "pnl", "pnl_pct"}


def test_public_dashboard_has_no_private_fields(client):
    data = client.get("/api/public/dashboard").json()

    asset = data["assets"][0]
    assert not PRIVATE_KEYS.intersection(asset.keys())
    assert asset["ticker"] == "aapl.us"
    assert asset["price"] == 229.87
    assert len(asset["history"]) == 2


def test_public_dashboard_reports_override_price(client, conn):
    db.upsert_asset(conn, {"ticker": "aapl.us", "name": "Apple", "kind": "stock", "quantity": 10, "avg_buy": 200, "override_price": 500.0})

    data = client.get("/api/public/dashboard").json()

    assert data["assets"][0]["price"] == 500.0


def test_admin_requires_auth(client):
    r = client.get("/admin")

    assert r.status_code == 401
    assert r.headers["www-authenticate"].startswith("Basic")


def test_admin_with_bad_credentials_is_unauthorized(client):
    r = client.get("/api/admin/dashboard", auth=("hugo", "mal"))

    assert r.status_code == 401


def test_admin_with_good_credentials_returns_private_totals(client):
    r = client.get("/api/admin/dashboard", auth=AUTH)

    assert r.status_code == 200
    data = r.json()
    assert data["assets"][0]["quantity"] == 10
    assert data["totals"]["value"] == 2298.7
    assert data["totals"]["pnl"] == 298.7


def test_create_and_delete_asset_require_auth(client):
    payload = {"ticker": "msft.us", "name": "Microsoft", "kind": "stock", "quantity": 5, "avg_buy": 300, "override_price": None}

    assert client.post("/api/admin/assets", json=payload).status_code == 401
    assert client.post("/api/admin/assets", json=payload, auth=AUTH).status_code == 200
    assert client.delete("/api/admin/assets/msft.us").status_code == 401
    assert client.delete("/api/admin/assets/msft.us", auth=AUTH).status_code == 200


def test_refresh_endpoint_calls_refresh(client):
    called = {"n": 0}

    def fake(c):
        called["n"] += 1

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db.init_db(conn)
    app = main.create_app(conn=conn, refresh_fn=fake)

    assert TestClient(app).post("/api/admin/refresh", auth=AUTH).status_code == 200
    assert called["n"] == 1


def test_healthz_is_public(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_health_alias_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}
