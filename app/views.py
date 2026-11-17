"""Construcción de las respuestas pública y privada."""

from __future__ import annotations

import sqlite3

from app import db
from app.service import display_price


def _change_for(price, prev, fallback):
    if price is not None and prev:
        return (price - prev) / prev * 100
    return fallback


def public_dashboard(conn: sqlite3.Connection) -> dict:
    """Solo campos mostrables. Nunca cantidades, compras ni importes."""
    assets = []
    counts = {"stock": 0, "etf": 0}
    for asset in db.list_assets(conn):
        quote = db.get_quote(conn, asset["ticker"]) or {}
        price = display_price(asset, quote)
        counts[asset["kind"]] = counts.get(asset["kind"], 0) + 1
        assets.append(
            {
                "ticker": asset["ticker"],
                "name": asset["name"],
                "kind": asset["kind"],
                "price": price,
                "change_pct": _change_for(price, quote.get("prev_close"), quote.get("change_pct")),
                "currency": quote.get("currency") or "USD",
                "as_of": quote.get("as_of"),
                "error": quote.get("error"),
                "history": [{"date": d, "close": c} for d, c in db.get_history(conn, asset["ticker"])],
            }
        )
    return {
        "updated_at": db.get_meta(conn, "last_refresh"),
        "assets": assets,
        "by_kind": counts,
    }


def admin_dashboard(conn: sqlite3.Connection) -> dict:
    """Vista privada: incluye todo, con valor y P&L por activo."""
    assets = []
    for asset in db.list_assets(conn):
        quote = db.get_quote(conn, asset["ticker"]) or {}
        price = display_price(asset, quote)
        qty = asset["quantity"] or 0
        value = (price or 0) * qty
        cost = (asset["avg_buy"] or 0) * qty
        pnl = value - cost
        assets.append(
            {
                "id": asset["id"],
                "ticker": asset["ticker"],
                "name": asset["name"],
                "kind": asset["kind"],
                "quantity": qty,
                "avg_buy": asset["avg_buy"],
                "override_price": asset["override_price"],
                "price": price,
                "currency": quote.get("currency") or "USD",
                "api_price": quote.get("price"),
                "prev_close": quote.get("prev_close"),
                "change_pct": _change_for(price, quote.get("prev_close"), quote.get("change_pct")),
                "value": round(value, 2),
                "cost": round(cost, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl / cost * 100, 2) if cost else None,
                "as_of": quote.get("as_of"),
                "error": quote.get("error"),
                "history": [{"date": d, "close": c} for d, c in db.get_history(conn, asset["ticker"])],
            }
        )
    from app.service import portfolio_totals

    return {
        "updated_at": db.get_meta(conn, "last_refresh"),
        "assets": assets,
        "totals": portfolio_totals(assets),
        "by_kind": {"stock": sum(1 for a in assets if a["kind"] == "stock"), "etf": sum(1 for a in assets if a["kind"] == "etf")},
    }
