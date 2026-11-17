"""Reglas de negocio: qué se muestra y qué cálculos se hacen."""


def _round2(value):
    return round(value, 2) if value is not None else None


def display_price(asset: dict, quote: dict | None) -> float | None:
    """El precio manual (override) gana siempre sobre el dato de la API."""
    if asset.get("override_price") is not None:
        return asset["override_price"]
    if quote is None:
        return None
    return quote.get("price")


def change_from_history(history: list[tuple[str, float]]) -> tuple[float | None, float | None, float | None]:
    """Precio, cierre anterior y variación % a partir de los dos últimos cierres."""
    if not history:
        return None, None, None
    price = history[-1][1]
    if len(history) < 2:
        return price, None, None
    prev = history[-2][1]
    pct = ((price - prev) / prev * 100) if prev else None
    return price, prev, pct


def portfolio_totals(assets: list[dict]) -> dict:
    """Cada asset debe traer `quote` (o None). Calcula valor, coste y P&L."""
    value = 0.0
    cost = 0.0
    for asset in assets:
        price = asset.get("price") if "price" in asset else display_price(asset, asset.get("quote"))
        qty = asset.get("quantity") or 0
        if price is not None:
            value += price * qty
        cost += (asset.get("avg_buy") or 0) * qty
    pnl = value - cost
    pnl_pct = (pnl / cost * 100) if cost else None
    return {"value": _round2(value), "cost": _round2(cost), "pnl": _round2(pnl), "pnl_pct": _round2(pnl_pct)}
