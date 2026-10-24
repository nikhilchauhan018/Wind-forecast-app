# Wind forecast accuracy for UK day-ahead buying

Web app that shows a UK energy buyer (1) the latest national wind forecast available at the day-ahead decision time and (2) how accurate those forecasts were, with a recommended margin to keep.

**Live app:** `<add your Vercel URL here>`

**AI tools used:** Claude (Anthropic) and GitHub Copilot AI in VS Code were used transparently during this project to assist with product design, implementation, UI restructuring, test creation, code review, troubleshooting and documentation. The final code, decisions and validation were reviewed by the developer; automated suggestions were not accepted without review. Backend tests and the frontend production build were run locally, and the analysis logic was checked against the bundled Elexon data.

Data: Elexon BMRS, `FUELHH` (actual wind, `fuelType=WIND`) and `WINDFOR` (wind forecast). Contains BMRS data © Elexon Limited copyright and database right 2026.

## Files and directories

```
backend/
  app/main.py        FastAPI routes and input validation
  app/selector.py    Forecast selection: latest forecast published before the decision cutoff
  app/metrics.py     Comparison frame and metrics (MAE, RMSE, bias, MAPE, percentiles, breakdowns)
  app/data.py        Loads the data snapshot
  app/config.py      Assumptions and constants
  scripts/ingest.py  Builds the snapshot from the Elexon API (or from pre-downloaded JSON)
  data/              Snapshot: actuals.csv.gz, forecasts.csv.gz
  tests/             pytest tests
  Dockerfile
frontend/            React + TypeScript + Vite + Recharts dashboard (Dockerfile, nginx.conf)
api/index.py         Vercel serverless entry point (wraps the FastAPI app)
vercel.json          Vercel build and routing config
docker-compose.yml   Runs backend and frontend together
requirements.txt     Runtime Python dependencies used by Vercel
```

## Run locally

**Docker (recommended):**
```bash
docker compose up --build
```
Open http://localhost:8080 (API docs at http://localhost:8000/docs).

**Without Docker:**
```bash
# terminal 1
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend && npm install && npm run dev
```
Open http://localhost:5173 (Vite proxies `/api` to port 8000).

**Tests and checks:**
```bash
cd backend && python -m pytest -q              # unit + API integration tests
cd frontend && npm run lint      # TypeScript type check
cd frontend && npm run build     # production build
```

The backend tests use FastAPI's in-process `TestClient` against the real bundled
snapshot. This covers the dashboard request bundle (`compare`, summary metrics,
hour/wind/horizon breakdowns, histogram and procurement buffer), validation
boundaries, forecast cutoff leakage, and the two actual-to-forecast alignment
modes. No external Elexon call is made during tests.

**Rebuild the data snapshot (optional):**
```bash
cd backend
python scripts/ingest.py                                            # fetch from Elexon (public API, no key)
python scripts/ingest.py --from-files forecasts.json actuals.json   # use downloaded JSON
```

## Deploy to Vercel

1. Push this repo to GitHub.
2. In Vercel choose "Add New Project" and import it.
3. Leave the root directory as the repo root; `vercel.json` sets the build.
4. Deploy, then put the URL at the top of this README.

## Key assumptions

- **Scope:** decisions made in January 2026 are made on D-1, so delivery days are 2 Jan to 1 Feb 2026.
- **Decision time:** 09:00 UTC on D-1 by default (UTC equals UK time in January). It can be changed in the UI.
- **Forecast selection:** for each target hour, the forecast with the latest `publishTime` at or before the cutoff. Targets with no such forecast are dropped, never filled. A test checks that no forecast published after the cutoff is ever used.
- **Resolution:** WINDFOR is hourly and FUELHH is half-hourly. By default each forecast is compared with the actual at the same timestamp; the UI can switch to the average of the two half-hours (the difference in MAE is about 16 MW).
- **Error:** forecast minus actual. Positive means the forecast was too high, so the buyer must buy the gap.
- **Buffer:** the chosen percentile (default 90th) of the positive error, shown as MW of extra procurement.
- **MAPE** ignores hours where actual wind is below 1,000 MW.
- **Lead time analysis** uses all published forecasts with a lead time of 0 hours or more.

## Results at the default 09:00 cutoff (744 hours)

MAE 2,022 MW, RMSE 2,497 MW, bias +1,746 MW (forecast too high in 85% of hours), MAPE 21.9%, 90th percentile shortfall 4,154 MW. A 12:00 cutoff lowers the 90th percentile shortfall to 3,768 MW.

## API

`GET /api/meta`, `/api/compare`, `/api/metrics`, `/api/metrics/by-hour`, `/api/metrics/by-wind-level`, `/api/metrics/by-horizon`, `/api/error-histogram`, `/api/buffer`, `/api/health`.

Most take `start`, `end` (dates), `cutoff_hour` (0 to 23) and `align` (`exact` or `hourly_mean`). Dates outside 2 Jan to 1 Feb 2026 return 422.

## Product and technical flow

1. The React client loads `/api/meta` to discover the supported delivery window and
   default decision time.
2. Changing a control creates one query, and the client requests the dashboard
   bundle in parallel. An `AbortController` cancels stale requests while a new
   selection is loading.
3. FastAPI validates the date, cutoff and confidence bounds, then loads the
   cached snapshot. The selector keeps only the latest forecast published at or
   before the D-1 cutoff for each target hour, preventing look-ahead leakage.
4. The metrics layer aligns hourly WINDFOR forecasts with half-hourly FUELHH
   actuals, calculates error as `forecast - actual`, and returns summary and
   breakdown data.
5. The UI presents the procurement buffer, quantitative accuracy measures,
   charts/tables, and a CSV export for further review.

## Prioritised improvements

1. **Production data freshness:** schedule a monitored ingestion job and expose
   snapshot timestamp, source row counts and data-quality warnings in `/api/meta`.
2. **Decision-grade uncertainty:** backtest rolling months and report confidence
   intervals, calibration and seasonal/regime performance rather than relying on
   one January sample.
3. **Operational resilience:** add structured logs, request timing, dependency
   health checks, rate limiting and a non-wildcard production CORS allowlist.
4. **Performance and scale:** precompute common metric bundles, paginate or
   downsample chart rows, and code-split the Recharts bundle.
5. **Delivery quality:** add browser-level smoke tests for control changes,
   loading/error states and CSV download, plus CI that runs backend tests and the
   frontend build on every pull request.

## Design choices and trade-offs

- A bundled data snapshot keeps the deployed app fast and independent of Elexon being available; the ingest script keeps it reproducible.
- pandas does the selection and metrics in vectorised form, with no per-row loops.
- Known limits: one month of data and national level only, so percentile estimates are rough. Future work: live ingestion, other cutoffs compared side by side, price data.
