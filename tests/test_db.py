import sqlite3

import pytest

from app import db


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.init_db(c)
    yield c
    c.close()


def test_upsert_asset_inserts_and_updates(conn):
    db.upsert_asset(conn, {"ticker": "aapl.us", "name": "Apple", "kind": "stock", "quantity": 10, "avg_buy": 200.0, "override_price": None})
    db.upsert_asset(conn, {"ticker": "aapl.us", "name": "Apple Inc", "kind": "stock", "quantity": 12, "avg_buy": 210.0, "override_price": 100.0})

    rows = db.list_assets(conn)

    assert len(rows) == 1
    assert rows[0]["name"] == "Apple Inc"
    assert rows[0]["quantity"] == 12
    assert rows[0]["override_price"] == 100.0


def test_delete_asset_removes_it(conn):
    db.upsert_asset(conn, {"ticker": "aapl.us", "name": "Apple", "kind": "stock", "quantity": 1, "avg_buy": 1, "override_price": None})

    db.delete_asset(conn, "aapl.us")

    assert db.list_assets(conn) == []


def test_upsert_quote_and_history_round_trip(conn):
    db.upsert_quote(conn, "aapl.us", {"price": 229.87, "prev_close": 227.2, "change_pct": 1.17, "as_of": "2026-11-17", "error": None})
    db.replace_history(conn, "aapl.us", [("2026-11-14", 227.2), ("2026-11-17", 229.87)])

    quote = db.get_quote(conn, "aapl.us")
    history = db.get_history(conn, "aapl.us")

    assert quote["price"] == 229.87
    assert history == [("2026-11-14", 227.2), ("2026-11-17", 229.87)]


def test_meta_round_trip(conn):
    db.set_meta(conn, "last_refresh", "2026-11-17T18:00:00")

    assert db.get_meta(conn, "last_refresh") == "2026-11-17T18:00:00"
    assert db.get_meta(conn, "missing") is None
