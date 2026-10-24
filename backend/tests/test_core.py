import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.metrics import build_comparison, summarise
from app.selector import decision_cutoff, select_latest_before_cutoff

T = lambda s: pd.Timestamp(s, tz="UTC")


def _fc():
    # target 2026-01-05 12:00 has forecasts published before/after the 09:00 D-1 cutoff
    rows = [
        ("2026-01-05T12:00:00Z", "2026-01-04T02:30:00Z", 100),
        ("2026-01-05T12:00:00Z", "2026-01-04T07:30:00Z", 200),   # latest allowed
        ("2026-01-05T12:00:00Z", "2026-01-04T09:30:00Z", 999),   # after cutoff -> must be ignored
        ("2026-01-05T12:00:00Z", "2026-01-05T02:30:00Z", 888),   # same day -> must be ignored
    ]
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


def test_selector_latest_before_cutoff_no_leakage():
    sel = select_latest_before_cutoff(_fc(), 9)
    assert len(sel) == 1 and sel.loc[0, "generation"] == 200
    assert (sel["publishTime"] <= decision_cutoff(sel["startTime"], 9)).all()


def test_selector_drops_targets_without_forecast():
    assert select_latest_before_cutoff(_fc(), 1).empty


def test_metrics_known_values():
    df = pd.DataFrame({"error": [100.0, -100.0, 300.0, -300.0], "actual": [5000.0] * 4})
    m = summarise(df)
    assert m["mae"] == 200 and m["bias"] == 0 and np.isclose(m["rmse"], np.sqrt(50000))
    assert m["pct_over_forecast"] == 50


def test_comparison_joins_actuals():
    act = pd.DataFrame({"startTime": [T("2026-01-05T12:00:00Z")], "generation": [150.0]})
    df = build_comparison(act, _fc(), "2026-01-05", "2026-01-05", 9)
    assert df.loc[0, "error"] == 50


client = TestClient(app)


def test_api_metrics_and_validation():
    r = client.get("/api/metrics")
    assert r.status_code == 200 and r.json()["n"] > 600
    assert client.get("/api/metrics?start=2025-12-01").status_code == 422
    assert client.get("/api/metrics?cutoff_hour=30").status_code == 422
    assert client.get("/api/health").json() == {"status": "ok"}


def test_api_every_delivery_day_complete():
    rows = client.get("/api/compare").json()["rows"]
    assert len(rows) == 31 * 24


def test_api_dashboard_bundle_contract():
    params = {"start": "2026-01-05", "end": "2026-01-06", "cutoff_hour": 9, "align": "exact"}
    endpoints = [
        "/api/compare",
        "/api/metrics/by-hour",
        "/api/metrics/by-wind-level",
        "/api/error-histogram",
        "/api/metrics/by-horizon",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200, (endpoint, response.text)
        assert isinstance(response.json()["rows"], list)

    summary = client.get("/api/metrics", params=params)
    assert summary.status_code == 200
    assert summary.json()["n"] == 48

    buffer_response = client.get("/api/buffer", params={**params, "confidence": 0.95})
    assert buffer_response.status_code == 200
    buffer = buffer_response.json()
    assert buffer["confidence"] == 0.95
    assert buffer["n"] == summary.json()["n"]
    assert buffer["extra_procurement_mw"] >= 0


def test_api_rejects_invalid_date_order_and_confidence():
    assert client.get("/api/metrics", params={"start": "2026-01-06", "end": "2026-01-05"}).status_code == 422
    assert client.get("/api/buffer", params={"confidence": 0.4}).status_code == 422
    assert client.get("/api/buffer", params={"confidence": 1.0}).status_code == 422


def test_hourly_mean_alignment_is_exposed_by_api():
    params = {"start": "2026-01-05", "end": "2026-01-05", "align": "hourly_mean"}
    response = client.get("/api/compare", params=params)
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert len(rows) == 24
    assert all(row["t"].endswith(":00+00:00") for row in rows)
