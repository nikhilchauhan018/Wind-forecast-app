export const mw = (n: number | undefined | null): string =>
  n === undefined || n === null ? "n/a" : Math.round(n).toLocaleString("en-GB");

export const signed = (n: number | undefined): string =>
  n === undefined ? "n/a" : `${n >= 0 ? "+" : "-"}${Math.abs(Math.round(n)).toLocaleString("en-GB")}`;

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const stamp = (iso: string): string => {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${String(d.getUTCHours()).padStart(2, "0")}:00`;
};

export function toCsv(rows: { t: string; published: string; horizon_h: number; forecast: number; actual: number; error: number }[]): string {
  const head = "target_time_utc,forecast_published_utc,lead_time_h,forecast_mw,actual_mw,error_mw";
  return [head, ...rows.map((r) => [r.t, r.published, r.horizon_h, r.forecast, r.actual, r.error].join(","))].join("\n");
}
