"""Proveedor de datos público: Yahoo Finance (chart API, sin clave, sin realtime).

Aislado a propósito: si el proveedor cambia, solo se toca este fichero.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]


def chart_url(ticker: str, host: str = HOSTS[0]) -> str:
    return f"https://{host}/v8/finance/chart/{ticker}?range=5y&interval=1d"


def parse_chart_json(data: dict) -> dict:
    """Convierte la respuesta de Yahoo a {price, prev_close, as_of, currency, history}."""
    result = (data.get("chart") or {}).get("result")
    if not result:
        raise ValueError("respuesta sin datos")

    item = result[0]
    meta = item.get("meta") or {}
    timestamps = item.get("timestamp") or []
    closes = ((item.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []

    history = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        history.append((day, float(close)))

    price = meta.get("regularMarketPrice")
    if price is None and history:
        price = history[-1][1]

    # `chartPreviousClose` es el cierre de INICIO del rango (hace un año), no el de ayer.
    # La variación diaria se calcula con los dos últimos cierres del histórico.
    prev = meta.get("previousClose")
    if prev is None and len(history) >= 2:
        prev = history[-2][1]

    as_of = history[-1][0] if history else None
    if as_of is None and meta.get("regularMarketTime"):
        as_of = datetime.fromtimestamp(meta["regularMarketTime"], tz=timezone.utc).strftime("%Y-%m-%d")

    pct = ((price - prev) / prev * 100) if (price is not None and prev) else None
    return {
        "price": price,
        "prev_close": prev,
        "change_pct": pct,
        "as_of": as_of,
        "currency": meta.get("currency") or "USD",
        "history": history,
    }


def default_fetch_chart(ticker: str) -> dict:
    last_error = None
    for host in HOSTS:
        try:
            with httpx.Client(timeout=20, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, follow_redirects=True) as client:
                response = client.get(chart_url(ticker, host))
                response.raise_for_status()
                return parse_chart_json(response.json())
        except Exception as exc:
            last_error = exc
    raise last_error
