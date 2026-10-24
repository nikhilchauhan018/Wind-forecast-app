from datetime import date
from functools import lru_cache
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import metrics as M
from .config import DEFAULT_CUTOFF_HOUR_UTC, DELIVERY_END, DELIVERY_START
from .data import load_actuals, load_forecasts

app = FastAPI(title="Wind Forecast Accuracy API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

LO, HI = date.fromisoformat(DELIVERY_START), date.fromisoformat(DELIVERY_END)
Align = Literal["exact", "hourly_mean"]


def _check(start: date, end: date):
    if start > end:
        raise HTTPException(422, "start must be <= end")
    if start < LO or end > HI:
        raise HTTPException(422, f"Dates must be within {LO} .. {HI} (delivery days for January 2026 decisions)")


_comparison_cache_lock = Lock()


@lru_cache(maxsize=64)
def _build_cached_cmp(start: date, end: date, cutoff_hour: int, align: Align):
    return M.build_comparison(load_actuals(), load_forecasts(), start, end, cutoff_hour, align)


def _cached_cmp(start: date, end: date, cutoff_hour: int, align: Align):
    with _comparison_cache_lock:
        return _build_cached_cmp(start, end, cutoff_hour, align)


def _cmp(start, end, cutoff_hour, align):
    _check(start, end)
    return _cached_cmp(start, end, cutoff_hour, align)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return {
        "delivery_start": DELIVERY_START, "delivery_end": DELIVERY_END,
        "default_cutoff_hour_utc": DEFAULT_CUTOFF_HOUR_UTC,
        "source": "Elexon BMRS (FUELHH WIND actuals, WINDFOR forecasts)",
        "definition": "error = forecast - actual; positive error = over-forecast = wind shortfall to buy",
    }


@app.get("/api/compare")
def compare(start: date = LO, end: date = HI,
            cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23), align: Align = "exact"):
    df = _cmp(start, end, cutoff_hour, align)
    return {"rows": [
        {"t": r.startTime.isoformat(), "published": r.publishTime.isoformat(), "horizon_h": r.horizon_h,
         "forecast": r.forecast, "actual": r.actual, "error": r.error} for r in df.itertuples()]}


@app.get("/api/metrics")
def metrics(start: date = LO, end: date = HI,
            cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23), align: Align = "exact"):
    return M.summarise(_cmp(start, end, cutoff_hour, align))


@app.get("/api/metrics/by-hour")
def metrics_by_hour(start: date = LO, end: date = HI,
                    cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23), align: Align = "exact"):
    return {"rows": M.by_hour(_cmp(start, end, cutoff_hour, align))}


@app.get("/api/metrics/by-wind-level")
def metrics_by_wind(start: date = LO, end: date = HI,
                    cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23), align: Align = "exact"):
    return {"rows": M.by_wind_level(_cmp(start, end, cutoff_hour, align))}


@app.get("/api/error-histogram")
def error_histogram(start: date = LO, end: date = HI,
                    cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23), align: Align = "exact"):
    return {"rows": M.histogram(_cmp(start, end, cutoff_hour, align))}


@app.get("/api/metrics/by-horizon")
def metrics_by_horizon(start: date = LO, end: date = HI, align: Align = "exact"):
    _check(start, end)
    return {"rows": M.by_horizon(load_actuals(), load_forecasts(), start, end, align)}


@app.get("/api/buffer")
def buffer(start: date = LO, end: date = HI,
           cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR_UTC, ge=0, le=23),
           confidence: float = Query(0.9, ge=0.5, le=0.99), align: Align = "exact"):
    df = _cmp(start, end, cutoff_hour, align)
    if df.empty:
        raise HTTPException(404, "No data for selection")
    q = float(max(df["error"].quantile(confidence), 0.0))
    return {"confidence": confidence, "extra_procurement_mw": q, "n": int(len(df)),
            "message": f"With the forecast available at {cutoff_hour:02d}:00 UTC on D-1, plan to cover up to "
                       f"{q:,.0f} MW of extra wind shortfall to be {confidence:.0%} confident."}
