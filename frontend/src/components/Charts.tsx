import {
  Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, LineChart,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { mw, stamp } from "../format";
import type { CompareRow, HistRow, HorizonRow, HourRow } from "../types";

const C = {
  actual: "var(--actual)", forecast: "var(--forecast)", short: "var(--short)", long: "var(--long)", grid: "var(--grid)", text: "var(--muted)",
};
const axis = { stroke: C.text, fontSize: 12, tickLine: false } as const;
const tip = { contentStyle: { background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 6, fontSize: 13 } };
const kfmt = (v: number) => `${(v / 1000).toLocaleString("en-GB")}`;

export function ForecastVsActual({ rows }: { rows: CompareRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="t" tickFormatter={stamp} minTickGap={60} {...axis} />
        <YAxis tickFormatter={kfmt} width={44} {...axis} label={{ value: "GW", position: "insideTopLeft", offset: 8, fill: "var(--muted)", fontSize: 12 }} />
        <Tooltip {...tip} labelFormatter={(l: string) => `${stamp(l)} UTC`} formatter={(v: number, n: string) => [`${mw(v)} MW`, n]} />
        <Legend verticalAlign="top" height={28} />
        <Line type="monotone" dataKey="actual" name="Actual wind" stroke={C.actual} strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="forecast" name="Forecast at decision time" stroke={C.forecast} strokeWidth={2} dot={false} strokeDasharray="5 3" isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ErrorHistogram({ rows }: { rows: HistRow[] }) {
  const data = rows.map((r) => ({ ...r, label: `${kfmt(r.from_mw)}` }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 16, left: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="label" {...axis} label={{ value: "Forecast minus actual (GW, bin start)", position: "insideBottom", offset: -10, fill: "var(--muted)", fontSize: 12 }} />
        <YAxis width={36} {...axis} />
        <Tooltip {...tip} formatter={(v: number) => [`${v} hours`, "Count"]} labelFormatter={(l: string) => `From ${l} GW`} />
        <ReferenceLine x={kfmt(0)} stroke="var(--muted)" />
        <Bar dataKey="count" isAnimationActive={false}>
          {data.map((r) => <Cell key={r.from_mw} fill={r.from_mw >= 0 ? C.short : C.long} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ErrorByHorizon({ rows }: { rows: HorizonRow[] }) {
  const data = rows.map((r) => ({ label: `${r.horizon_from_h}-${r.horizon_to_h}`, mae: r.mae, bias: r.bias, n: r.n }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 16, left: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="label" {...axis} label={{ value: "Hours between publication and target hour", position: "insideBottom", offset: -10, fill: "var(--muted)", fontSize: 12 }} />
        <YAxis tickFormatter={kfmt} width={36} {...axis} />
        <Tooltip {...tip} formatter={(v: number, n: string) => [`${mw(v)} MW`, n]} />
        <Legend verticalAlign="top" height={28} />
        <Bar dataKey="mae" name="Mean absolute error" fill={C.forecast} isAnimationActive={false} />
        <Line dataKey="bias" name="Bias" stroke={C.short} strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function ErrorByHour({ rows }: { rows: HourRow[] }) {
  const data = rows.map((r) => ({ label: String(r.hour).padStart(2, "0"), mae: r.mae, bias: r.bias }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 16, left: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="label" {...axis} label={{ value: "Delivery hour (UTC)", position: "insideBottom", offset: -10, fill: "var(--muted)", fontSize: 12 }} />
        <YAxis tickFormatter={kfmt} width={36} {...axis} />
        <Tooltip {...tip} formatter={(v: number, n: string) => [`${mw(v)} MW`, n]} />
        <Legend verticalAlign="top" height={28} />
        <Bar dataKey="mae" name="Mean absolute error" fill={C.forecast} isAnimationActive={false} />
        <Line dataKey="bias" name="Bias" stroke={C.short} strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
