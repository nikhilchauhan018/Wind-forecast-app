"""Load the Elexon snapshot (CSV.GZ) created by scripts/ingest.py."""
from functools import lru_cache

import pandas as pd

from .config import DATA_DIR


@lru_cache(maxsize=1)
def load_actuals() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "actuals.csv.gz")
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df.drop_duplicates("startTime", keep="last").sort_values("startTime").reset_index(drop=True)


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "forecasts.csv.gz")
    for c in ("startTime", "publishTime"):
        df[c] = pd.to_datetime(df[c], utc=True)
    df = df.drop_duplicates(["startTime", "publishTime"], keep="last")
    return df.sort_values(["startTime", "publishTime"]).reset_index(drop=True)
