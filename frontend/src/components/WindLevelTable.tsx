import { mw, signed } from "../format";
import type { WindRow } from "../types";

export default function WindLevelTable({ rows }: { rows: WindRow[] }) {
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr><th>Actual wind level</th><th>Hours</th><th>Mean abs. error (MW)</th><th>Bias (MW)</th><th>90th pct shortfall (MW)</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.level}>
              <td>{r.level}</td><td>{r.n}</td><td>{mw(r.mae)}</td><td>{signed(r.bias)}</td><td>{mw(r.p90_shortfall)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
