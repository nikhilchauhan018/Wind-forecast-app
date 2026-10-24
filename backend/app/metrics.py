"""Comparison frame + error metrics. Error = forecast - actual (positive = over-forecast)."""
import numpy as np
import pandas as pd

from .config import HORIZON_BIN_H, MAPE_MIN_ACTUAL_MW, WIND_BINS, WIND_LABELS
from .selector import select_latest_before_cutoff


def align_actuals(actuals: pd.DataFrame, mode: str = "exact") -> pd.DataFrame:
    """WINDFOR is hourly, FUELHH is half-hourly.
    exact: use the actual at the same :00 timestamp. hourly_mean: mean of :00 and :30."""
    a = actuals[["startTime", "generation"]].rename(columns={"generation": "actual"})
    if mode == "hourly_mean":
        a = a.assign(startTime=a["startTime"].dt.floor("h")).groupby("startTime", as_index=False)["actual"].mean()
    return a


def _window(start, end):
    return pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)


def build_comparison(actuals, forecasts, start, end, cutoff_hour, align="exact") -> pd.DataFrame:
    sel = select_latest_before_cutoff(forecasts, cutoff_hour)
    lo, hi = _window(start, end)
    sel = sel[(sel["startTime"] >= lo) & (sel["startTime"] < hi)]
    df = sel.merge(align_actuals(actuals, align), on="startTime", how="inner")
    df = df.rename(columns={"generation": "forecast"})
    df["error"] = df["forecast"] - df["actual"]
    return df[["startTime", "publishTime", "horizon_h", "forecast", "actual", "error"]]


def summarise(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n": 0}
    e, a = df["error"], df["actual"]
    ae = e.abs()
    m = a >= MAPE_MIN_ACTUAL_MW
    return {
        "n": int(len(df)),
        "mae": float(ae.mean()),
        "rmse": float(np.sqrt((e ** 2).mean())),
        "bias": float(e.mean()),
        "mape_pct": float((ae[m] / a[m]).mean() * 100) if m.any() else None,
        "p50_abs": float(ae.quantile(0.5)),
        "p90_abs": float(ae.quantile(0.9)),
        "p95_abs": float(ae.quantile(0.95)),
        # Over-forecast (forecast > actual) = wind shortfall the buyer must cover.
        "p90_shortfall": float(max(e.quantile(0.9), 0.0)),
        "p95_shortfall": float(max(e.quantile(0.95), 0.0)),
        "pct_over_forecast": float((e > 0).mean() * 100),
    }


def by_hour(df: pd.DataFrame) -> list[dict]:
    g = df.assign(hour=df["startTime"].dt.hour).groupby("hour")
    return [{"hour": int(h), **summarise(x)} for h, x in g]


def by_wind_level(df: pd.DataFrame) -> list[dict]:
    lvl = pd.cut(df["actual"], WIND_BINS, labels=WIND_LABELS, right=False)
    return [{"level": str(k), **summarise(x)} for k, x in df.groupby(lvl, observed=True)]


def by_horizon(actuals, forecasts, start, end, align="exact") -> list[dict]:
    """Error vs lead time across ALL published forecasts (horizon >= 0)."""
    lo, hi = _window(start, end)
    f = forecasts[(forecasts["startTime"] >= lo) & (forecasts["startTime"] < hi)]
    df = f.merge(align_actuals(actuals, align), on="startTime", how="inner")
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    df = df[df["horizon_h"] >= 0].copy()
    df["error"] = df["generation"] - df["actual"]
    df["bin"] = (df["horizon_h"] // HORIZON_BIN_H * HORIZON_BIN_H).astype(int)
    return [{"horizon_from_h": int(b), "horizon_to_h": int(b + HORIZON_BIN_H), **summarise(x)}
            for b, x in df.groupby("bin")]


def histogram(df: pd.DataFrame, bin_mw: int = 1000) -> list[dict]:
    if df.empty:
        return []
    lo = int(np.floor(df["error"].min() / bin_mw) * bin_mw)
    hi = int(np.ceil(df["error"].max() / bin_mw) * bin_mw) + bin_mw
    cnt, edges = np.histogram(df["error"], bins=np.arange(lo, hi + 1, bin_mw))
    return [{"from_mw": int(edges[i]), "to_mw": int(edges[i + 1]), "count": int(c)} for i, c in enumerate(cnt)]
