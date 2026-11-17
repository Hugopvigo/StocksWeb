"""Orquestación de la actualización horaria. Aísla la red del resto de la app."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app import db
from app.provider import default_fetch_chart


def refresh(conn: sqlite3.Connection, fetch_chart=default_fetch_chart) -> dict:
    """Actualiza cotizaciones e histórico. Un fallo por ticker no rompe el barrido."""
    assets = db.list_assets(conn)
    if not assets:
        db.set_meta(conn, "last_refresh", datetime.now(timezone.utc).isoformat())
        return {"ok": 0, "failed": 0}

    ok = 0
    failed = 0
    for asset in assets:
        ticker = asset["ticker"]
        old = db.get_quote(conn, ticker) or {}
        try:
            data = fetch_chart(ticker)
            if not data or data.get("price") is None:
                raise ValueError("sin precio")
            db.replace_history(conn, ticker, data.get("history") or [])
            db.upsert_quote(conn, ticker, {**data, "error": None})
            ok += 1
        except Exception as exc:
            db.upsert_quote(
                conn,
                ticker,
                {
                    "price": old.get("price"),
                    "prev_close": old.get("prev_close"),
                    "change_pct": old.get("change_pct"),
                    "as_of": old.get("as_of"),
                    "error": f"{type(exc).__name__}: {exc}"[:180],
                },
            )
            failed += 1

    db.set_meta(conn, "last_refresh", datetime.now(timezone.utc).isoformat())
    return {"ok": ok, "failed": failed}
