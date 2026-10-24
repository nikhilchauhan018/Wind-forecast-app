import type { Meta, Query } from "../types";

interface Props { meta: Meta; q: Query; onChange: (q: Query) => void; disabled: boolean }

export default function Controls({ meta, q, onChange, disabled }: Props) {
  const set = <K extends keyof Query>(k: K, v: Query[K]) => onChange({ ...q, [k]: v });
  return (
    <form className="controls" onSubmit={(e) => e.preventDefault()} aria-label="Report settings">
      <label>
        Delivery from
        <input type="date" value={q.start} min={meta.delivery_start} max={q.end} disabled={disabled}
          onChange={(e) => e.target.value && set("start", e.target.value)} />
      </label>
      <label>
        Delivery to
        <input type="date" value={q.end} min={q.start} max={meta.delivery_end} disabled={disabled}
          onChange={(e) => e.target.value && set("end", e.target.value)} />
      </label>
      <label>
        Buying decision at (UTC, day before)
        <select value={q.cutoffHour} disabled={disabled} onChange={(e) => set("cutoffHour", Number(e.target.value))}>
          {Array.from({ length: 24 }, (_, h) => (
            <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
          ))}
        </select>
      </label>
      <label>
        Confidence for buffer
        <select value={q.confidence} disabled={disabled} onChange={(e) => set("confidence", Number(e.target.value))}>
          <option value={0.8}>80%</option>
          <option value={0.9}>90%</option>
          <option value={0.95}>95%</option>
        </select>
      </label>
      <label>
        Actuals matched to forecast hour
        <select value={q.align} disabled={disabled} onChange={(e) => set("align", e.target.value as Query["align"])}>
          <option value="exact">Same timestamp</option>
          <option value="hourly_mean">Average of two half-hours</option>
        </select>
      </label>
    </form>
  );
}
