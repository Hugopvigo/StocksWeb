"""Acceso a SQLite. Un único fichero, sin ORM."""

from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'stock',
    quantity REAL NOT NULL DEFAULT 0,
    avg_buy REAL NOT NULL DEFAULT 0,
    override_price REAL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS quotes (
    ticker TEXT PRIMARY KEY,
    price REAL,
    prev_close REAL,
    change_pct REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    as_of TEXT,
    error TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS history (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL NOT NULL,
    PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


ASSET_FIELDS = ("ticker", "name", "kind", "quantity", "avg_buy", "override_price")


def upsert_asset(conn: sqlite3.Connection, data: dict) -> None:
    values = [data.get(field) for field in ASSET_FIELDS]
    do_update = ", ".join(f"{field}=excluded.{field}" for field in ASSET_FIELDS if field != "ticker")
    conn.execute(
        f"INSERT INTO assets ({', '.join(ASSET_FIELDS)}) VALUES (?, ?, ?, ?, ?, ?) "
        f"ON CONFLICT(ticker) DO UPDATE SET {do_update}",
        values,
    )
    conn.commit()


def list_assets(conn: sqlite3.Connection):
    return [dict(row) for row in conn.execute("SELECT * FROM assets WHERE active=1 ORDER BY ticker")]


def delete_asset(conn: sqlite3.Connection, ticker: str) -> None:
    conn.execute("DELETE FROM assets WHERE ticker=?", (ticker,))
    conn.execute("DELETE FROM quotes WHERE ticker=?", (ticker,))
    conn.execute("DELETE FROM history WHERE ticker=?", (ticker,))
    conn.commit()


def upsert_quote(conn: sqlite3.Connection, ticker: str, quote: dict) -> None:
    conn.execute(
        "INSERT INTO quotes (ticker, price, prev_close, change_pct, as_of, error, currency) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(ticker) DO UPDATE SET price=excluded.price, prev_close=excluded.prev_close, "
        "change_pct=excluded.change_pct, as_of=excluded.as_of, error=excluded.error, currency=excluded.currency, updated_at=datetime('now')",
        (ticker, quote.get("price"), quote.get("prev_close"), quote.get("change_pct"), quote.get("as_of"), quote.get("error"), quote.get("currency") or "USD"),
    )
    conn.commit()


def get_quote(conn: sqlite3.Connection, ticker: str):
    row = conn.execute("SELECT * FROM quotes WHERE ticker=?", (ticker,)).fetchone()
    return dict(row) if row else None


def replace_history(conn: sqlite3.Connection, ticker: str, rows: list[tuple[str, float]]) -> None:
    conn.execute("DELETE FROM history WHERE ticker=?", (ticker,))
    conn.executemany("INSERT INTO history (ticker, date, close) VALUES (?, ?, ?)", [(ticker, d, c) for d, c in rows])
    conn.commit()


def get_history(conn: sqlite3.Connection, ticker: str) -> list[tuple[str, float]]:
    rows = conn.execute("SELECT date, close FROM history WHERE ticker=? ORDER BY date", (ticker,)).fetchall()
    return [(row["date"], row["close"]) for row in rows]


def get_meta(conn: sqlite3.Connection, key: str):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit()
