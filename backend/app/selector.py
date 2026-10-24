"""Forecast selection: the latest forecast available at the day-ahead decision time."""
import pandas as pd


def decision_cutoff(start_time: pd.Series, cutoff_hour: float) -> pd.Series:
    """Cutoff for each target = (00:00 UTC of delivery day) - 1 day + cutoff_hour."""
    day = start_time.dt.floor("D")
    return day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)


def select_latest_before_cutoff(forecasts: pd.DataFrame, cutoff_hour: float) -> pd.DataFrame:
    """For every target startTime keep the row with the max publishTime <= cutoff.

    Targets with no forecast published before the cutoff are dropped (never filled).
    Guarantee: returned publishTime is never after the cutoff (no look-ahead leakage).
    """
    f = forecasts.copy()
    f["cutoff"] = decision_cutoff(f["startTime"], cutoff_hour)
    f = f[f["publishTime"] <= f["cutoff"]]
    f = f.sort_values("publishTime").groupby("startTime", as_index=False).tail(1)
    f["horizon_h"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600
    return f.sort_values("startTime").reset_index(drop=True)
