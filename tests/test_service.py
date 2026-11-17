from app import service


ASSET = {
    "id": 1,
    "ticker": "aapl.us",
    "name": "Apple",
    "kind": "stock",
    "quantity": 10,
    "avg_buy": 200.0,
    "override_price": None,
}

QUOTE = {"price": 229.87, "prev_close": 227.2, "change_pct": 1.17, "as_of": "2026-11-17", "error": None}


def test_display_price_uses_api_price_when_no_override():
    assert service.display_price(ASSET, QUOTE) == 229.87


def test_display_price_uses_override_when_set():
    asset = {**ASSET, "override_price": 999.0}

    assert service.display_price(asset, QUOTE) == 999.0


def test_display_price_is_none_when_no_data_at_all():
    assert service.display_price(ASSET, None) is None


def test_change_from_history_uses_two_last_closes():
    history = [("2026-11-14", 227.2), ("2026-11-17", 229.87)]

    price, prev, pct = service.change_from_history(history)

    assert price == 229.87
    assert prev == 227.2
    assert round(pct, 2) == 1.18


def test_change_from_history_with_one_point_has_no_change():
    price, prev, pct = service.change_from_history([("2026-11-17", 229.87)])

    assert price == 229.87
    assert prev is None
    assert pct is None


def test_change_from_history_with_empty_history_is_safe():
    assert service.change_from_history([]) == (None, None, None)


def test_portfolio_totals_compute_value_cost_and_pnl():
    assets = [{**ASSET, "quantity": 10, "avg_buy": 200.0, "quote": QUOTE}]
    totals = service.portfolio_totals(assets)

    assert totals["value"] == 2298.7
    assert totals["cost"] == 2000.0
    assert round(totals["pnl"], 2) == 298.7
    assert round(totals["pnl_pct"], 2) == 14.93
