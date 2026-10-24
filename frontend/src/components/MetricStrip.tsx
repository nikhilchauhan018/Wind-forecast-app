import { mw, signed } from "../format";
import type { Summary } from "../types";

export default function MetricStrip({ s }: { s: Summary }) {
  const items = [
    { k: "Mean absolute error", v: `${mw(s.mae)} MW`, d: "Typical size of a miss, in either direction." },
    { k: "RMSE", v: `${mw(s.rmse)} MW`, d: "Like the mean error, but large misses count more." },
    { k: "Bias", v: `${signed(s.bias)} MW`, d: "Average of forecast minus actual. Positive means the forecast ran high." },
    { k: "MAPE", v: s.mape_pct == null ? "n/a" : `${s.mape_pct.toFixed(1)}%`, d: "Percentage error. Hours below 1,000 MW of actual wind are left out." },
    { k: "Hours forecast too high", v: `${(s.pct_over_forecast ?? 0).toFixed(0)}%`, d: "Share of hours where you would have had to buy extra." },
    { k: "Hours compared", v: mw(s.n), d: "Hourly targets with both a forecast and an actual." },
  ];
  return (
    <dl className="strip">
      {items.map((i) => (
        <div key={i.k}>
          <dt>{i.k}</dt>
          <dd>{i.v}</dd>
          <dd className="note">{i.d}</dd>
        </div>
      ))}
    </dl>
  );
}
