"""Central configuration and assumptions (all documented in the README)."""
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
# Decisions made in January 2026 (on D-1) cover delivery days 2 Jan .. 1 Feb 2026.
DELIVERY_START = "2026-01-02"
DELIVERY_END = "2026-02-01"
DEFAULT_CUTOFF_HOUR_UTC = 9      # day-ahead decision time on D-1 (UTC == UK time in January)
MAPE_MIN_ACTUAL_MW = 1000.0      # actuals below this are excluded from MAPE
WIND_BINS = [0, 6000, 12000, float("inf")]
WIND_LABELS = ["Low (<6 GW)", "Medium (6-12 GW)", "High (>12 GW)"]
HORIZON_BIN_H = 6
