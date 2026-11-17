import sqlite3

import pytest

from app import db, market


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.init_db(c)
    db.upsert_asset(c, {"ticker": "AAPL", "name": "Apple", "kind": "stock", "quantity": 10, "avg_buy": 200, "override_price": None})
    db.upsert_asset(c, {"ticker": "BAD", "name": "Bad", "kind": "etf", "quantity": 1, "avg_buy": 1, "override_price": None})
    yield c
    c.close()


CHART = {
    "price": 229.87,
    "prev_close": 227.2,
    "change_pct": 1.17,
    "as_of": "2026-11-17",
    "currency": "USD",
    "history": [("2026-11-14", 227.2), ("2026-11-17", 229.87)],
}


def fake_chart(ticker):
    if ticker == "AAPL":
        return CHART
    raise RuntimeError("sin datos")


def test_refresh_stores_quote_history_and_change(conn):
    result = market.refresh(conn, fetch_chart=fake_chart)

    quote = db.get_quote(conn, "AAPL")
    assert result == {"ok": 1, "failed": 1}
    assert quote["price"] == 229.87
    assert quote["prev_close"] == 227.2
    assert round(quote["change_pct"], 2) == 1.17
    assert quote["currency"] == "USD"
    assert db.get_history(conn, "AAPL") == [("2026-11-14", 227.2), ("2026-11-17", 229.87)]
    assert db.get_meta(conn, "last_refresh") is not None


def test_refresh_records_error_without_crashing_other_assets(conn):
    market.refresh(conn, fetch_chart=fake_chart)

    assert "sin datos" in db.get_quote(conn, "BAD")["error"]
    assert db.get_quote(conn, "AAPL")["price"] == 229.87


def test_refresh_keeps_last_price_when_fetch_fails(conn):
    db.upsert_quote(conn, "AAPL", {"price": 100.0, "prev_close": 99.0, "change_pct": 1.0, "as_of": "2026-11-16", "error": None})

    def always_fail(ticker):
        raise RuntimeError("red caída")

    market.refresh(conn, fetch_chart=always_fail)

    assert db.get_quote(conn, "AAPL")["price"] == 100.0
    assert "red caída" in db.get_quote(conn, "AAPL")["error"]
