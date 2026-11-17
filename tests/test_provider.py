from app import provider


def chart_payload():
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "EUR",
                        "regularMarketPrice": 45.21,
                        "chartPreviousClose": 40.0,
                        "regularMarketTime": 1763385600,
                    },
                    "timestamp": [1763049600, 1763136000, 1763222400],
                    "indicators": {"quote": [{"close": [44.1, 44.9, 45.21]}]},
                }
            ]
        }
    }


def test_parse_chart_json_uses_previous_day_close_not_range_start():
    out = provider.parse_chart_json(chart_payload())

    assert out["price"] == 45.21
    assert out["prev_close"] == 44.9
    assert out["currency"] == "EUR"
    assert round(out["change_pct"], 2) == 0.69


def test_parse_chart_json_builds_history_with_iso_dates():
    out = provider.parse_chart_json(chart_payload())

    assert [d for d, _ in out["history"]] == ["2025-11-13", "2025-11-14", "2025-11-15"]
    assert out["history"][-1][1] == 45.21


def test_parse_chart_json_skips_null_closes():
    data = chart_payload()
    data["chart"]["result"][0]["indicators"]["quote"][0]["close"] = [44.1, None, 45.21]

    out = provider.parse_chart_json(data)

    assert len(out["history"]) == 2


def test_parse_chart_json_raises_on_empty_result():
    try:
        provider.parse_chart_json({"chart": {"result": []}})
    except ValueError:
        return
    raise AssertionError(" debería lanzar ValueError")


def test_chart_url_points_to_public_endpoint():
    url = provider.chart_url("AAPL")

    assert "query1.finance.yahoo.com" in url
    assert "/v8/finance/chart/AAPL" in url
    assert "range=5y" in url
