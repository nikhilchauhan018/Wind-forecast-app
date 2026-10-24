import { useEffect, useMemo, useState } from "react";
import { fetchBundle, fetchMeta } from "./api";
import Controls from "./components/Controls";
import { ErrorByHorizon, ErrorByHour, ErrorHistogram, ForecastVsActual } from "./components/Charts";
import MetricStrip from "./components/MetricStrip";
import WindLevelTable from "./components/WindLevelTable";
import { mw, toCsv } from "./format";
import type { Bundle, Meta, Query } from "./types";

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [q, setQ] = useState<Query | null>(null);
  const [data, setData] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    fetchMeta()
      .then((m) => {
        setMeta(m);
        setQ({ start: m.delivery_start, end: m.delivery_end, cutoffHour: m.default_cutoff_hour_utc, align: "exact", confidence: 0.9 });
      })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, [attempt]);

  useEffect(() => {
    if (!q) return;
    const ctl = new AbortController();
    setLoading(true);
    setError(null);
    fetchBundle(q, ctl.signal)
      .then((b) => { setData(b); setLoading(false); })
      .catch((e: Error) => { if (e.name !== "AbortError") { setError(e.message); setLoading(false); } });
    return () => ctl.abort();
  }, [q]);

  const headline = useMemo(() => {
    if (!data?.buffer || !q) return null;
    const c = String(q.cutoffHour).padStart(2, "0");
    return {
      main: `Plan to cover up to ${mw(data.buffer.extra_procurement_mw)} MW of extra wind shortfall.`,
      sub: `Using the latest forecast published by ${c}:00 UTC on the day before delivery, the forecast was no more than this much above actual wind in ${Math.round(q.confidence * 100)}% of hours.`,
    };
  }, [data, q]);

  const download = () => {
    if (!data) return;
    const url = URL.createObjectURL(new Blob([toCsv(data.rows)], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: "wind_forecast_vs_actual.csv" });
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page">
      <header>
        <div className="brand-row">
          <div>
            <p className="eyebrow">GB POWER PROCUREMENT / PILOT</p>
            <h1>Wind forecast accuracy</h1>
          </div>
          <span className="status-pill"><span className="status-dot" /> Snapshot ready</span>
        </div>
        <p className="lede">A decision-support view for day-ahead buying: understand the latest wind forecast, compare it with actual generation, and quantify the margin to keep.</p>
      </header>

      {meta && q && (
        <section className="control-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">REPORT SETTINGS</p>
              <h3>Set the buying decision context</h3>
            </div>
            <p className="small">January 2026 delivery decisions · UTC</p>
          </div>
          <Controls meta={meta} q={q} onChange={setQ} disabled={false} />
        </section>
      )}

      {error && (
        <div className="notice error" role="alert">
          <strong>Could not load data.</strong> {error}
          <button onClick={() => (meta ? setQ(q ? { ...q } : q) : setAttempt((n) => n + 1))}>Try again</button>
        </div>
      )}

      {loading && !data && <div className="notice" role="status">Loading forecasts and actuals…</div>}

      {data && data.summary.n === 0 && !error && (
        <div className="notice">No hours match these settings. Widen the delivery dates or change the decision time.</div>
      )}

      {data && data.summary.n > 0 && (
        <main className={loading ? "busy" : ""} aria-busy={loading}>
          {headline && (
            <section className="hero">
              <p className="eyebrow">RECOMMENDED PROCUREMENT COVER</p>
              <h2>{headline.main}</h2>
              <p>{headline.sub}</p>
              <p className="small">
                A forecast higher than actual wind means you buy the gap on the day. This is the {Math.round((q?.confidence ?? 0.9) * 100)}th
                percentile of that gap, not a worst case.
              </p>
            </section>
          )}

          <MetricStrip s={data.summary} />

          <section className="panel primary-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">PRIMARY VIEW</p>
                <h3>Forecast at decision time vs actual wind</h3>
              </div>
              <button onClick={download}>Download CSV</button>
            </div>
            <p className="small">The orange line is the information available when the day-ahead purchase decision was made. The dark line is what was generated.</p>
            <ForecastVsActual rows={data.rows} />
          </section>

          <div className="grid analysis-grid">
            <section className="panel">
              <p className="eyebrow">ERROR DISTRIBUTION</p>
              <h3>How far off the forecast was</h3>
              <p className="small">Red bars are hours with a shortfall to buy; green bars are hours with surplus wind.</p>
              <ErrorHistogram rows={data.hist} />
            </section>
            <section className="panel">
              <p className="eyebrow">LEAD TIME</p>
              <h3>Error by lead time</h3>
              <p className="small">All forecasts published before the target hour, in 6-hour groups.</p>
              <ErrorByHorizon rows={data.horizon} />
            </section>
            <section className="panel">
              <p className="eyebrow">DELIVERY PROFILE</p>
              <h3>Error by delivery hour</h3>
              <p className="small">Which hours of the day are hardest to forecast.</p>
              <ErrorByHour rows={data.hours} />
            </section>
            <section className="panel">
              <p className="eyebrow">WIND REGIME</p>
              <h3>Error by wind level</h3>
              <p className="small">Windy hours carry the largest misses.</p>
              <WindLevelTable rows={data.wind} />
            </section>
          </div>
        </main>
      )}

      <footer>
        <p>
          Error is forecast minus actual. Forecast: Elexon WINDFOR (hourly). Actual: Elexon FUELHH, fuel type WIND.
          Times are UTC, which equals UK time in January.
        </p>
        <p>Contains BMRS data © Elexon Limited copyright and database right 2026.</p>
      </footer>
    </div>
  );
}
