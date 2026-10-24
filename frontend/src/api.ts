import type { Buffer, Bundle, CompareRow, HistRow, HorizonRow, HourRow, Meta, Query, Summary, WindRow } from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";

async function get<T>(path: string, params: Record<string, string | number>, signal?: AbortSignal): Promise<T> {
  const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  const res = await fetch(`${BASE}${path}?${qs}`, { signal });
  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch { /* keep statusText */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const fetchMeta = (): Promise<Meta> => get<Meta>("/meta", {});

export async function fetchBundle(q: Query, signal?: AbortSignal): Promise<Bundle> {
  const p = { start: q.start, end: q.end, cutoff_hour: q.cutoffHour, align: q.align };
  const [summary, cmp, hours, wind, horizon, hist, buffer] = await Promise.all([
    get<Summary>("/metrics", p, signal),
    get<{ rows: CompareRow[] }>("/compare", p, signal),
    get<{ rows: HourRow[] }>("/metrics/by-hour", p, signal),
    get<{ rows: WindRow[] }>("/metrics/by-wind-level", p, signal),
    get<{ rows: HorizonRow[] }>("/metrics/by-horizon", { start: q.start, end: q.end, align: q.align }, signal),
    get<{ rows: HistRow[] }>("/error-histogram", p, signal),
    get<Buffer>("/buffer", { ...p, confidence: q.confidence }, signal).catch(() => null),
  ]);
  return { summary, rows: cmp.rows, hours: hours.rows, wind: wind.rows, horizon: horizon.rows, hist: hist.rows, buffer };
}
