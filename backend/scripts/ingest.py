"""Build the data snapshot used by the API.

Usage:
  python scripts/ingest.py                      # fetch from Elexon (public API, no key)
  python scripts/ingest.py --from-files FORECASTS.json ACTUALS.json   # use pre-downloaded JSON
Outputs data/forecasts.csv.gz and data/actuals.csv.gz
"""
import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parent.parent / "data"


def get(path: str, params: dict) -> list[dict]:
    for attempt in range(4):
        r = requests.get(f"{BASE}/{path}", params=params, timeout=90)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Elexon rate limit")


def chunks(start: datetime, end: datetime, days: int = 7):
    while start < end:
        nxt = min(start + timedelta(days=days), end)
        yield start, nxt
        start = nxt


def fetch_forecasts():
    # Forecasts published 30 Dec 2025 .. 31 Jan 2026 cover every January decision.
    s = datetime(2025, 12, 30, tzinfo=timezone.utc)
    e = datetime(2026, 2, 1, tzinfo=timezone.utc)
    rows = []
    for a, b in chunks(s, e):
        rows += get("WINDFOR/stream", {"publishDateTimeFrom": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                       "publishDateTimeTo": b.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return rows


def fetch_actuals():
    rows = []
    for a, b in chunks(datetime(2026, 1, 1), datetime(2026, 2, 2)):
        rows += get("FUELHH/stream", {"settlementDateFrom": a.date().isoformat(),
                                      "settlementDateTo": (b - timedelta(days=1)).date().isoformat(),
                                      "fuelType": "WIND"})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-files", nargs=2, metavar=("FORECASTS", "ACTUALS"))
    args = ap.parse_args()
    if args.from_files:
        f_rows, a_rows = (json.load(open(p)) for p in args.from_files)
    else:
        f_rows, a_rows = fetch_forecasts(), fetch_actuals()

    f = pd.DataFrame(f_rows)[["startTime", "publishTime", "generation"]]
    a = pd.DataFrame(a_rows)
    a = a[a["fuelType"] == "WIND"][["startTime", "generation"]]
    f = f.drop_duplicates(["startTime", "publishTime"], keep="last").dropna()
    a = a.drop_duplicates("startTime", keep="last").dropna()
    OUT.mkdir(exist_ok=True)
    f.sort_values(["publishTime", "startTime"]).to_csv(OUT / "forecasts.csv.gz", index=False)
    a.sort_values("startTime").to_csv(OUT / "actuals.csv.gz", index=False)
    print(f"forecasts: {len(f)} rows, actuals: {len(a)} rows -> {OUT}")


if __name__ == "__main__":
    main()
