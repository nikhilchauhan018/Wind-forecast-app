export interface Summary {
  n: number;
  mae?: number;
  rmse?: number;
  bias?: number;
  mape_pct?: number | null;
  p50_abs?: number;
  p90_abs?: number;
  p95_abs?: number;
  p90_shortfall?: number;
  p95_shortfall?: number;
  pct_over_forecast?: number;
}
export interface CompareRow { t: string; published: string; horizon_h: number; forecast: number; actual: number; error: number }
export interface HourRow extends Summary { hour: number }
export interface WindRow extends Summary { level: string }
export interface HorizonRow extends Summary { horizon_from_h: number; horizon_to_h: number }
export interface HistRow { from_mw: number; to_mw: number; count: number }
export interface Buffer { confidence: number; extra_procurement_mw: number; n: number; message: string }
export interface Meta { delivery_start: string; delivery_end: string; default_cutoff_hour_utc: number }
export interface Query { start: string; end: string; cutoffHour: number; align: "exact" | "hourly_mean"; confidence: number }
export interface Bundle {
  summary: Summary; rows: CompareRow[]; hours: HourRow[]; wind: WindRow[];
  horizon: HorizonRow[]; hist: HistRow[]; buffer: Buffer | null;
}
