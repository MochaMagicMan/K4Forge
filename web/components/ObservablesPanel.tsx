"use client";

import type { Observable } from "@/lib/types";

function fmtSci(n: number | string): string {
  if (typeof n === 'string') return n === 'Infinity' ? '∞' : n;
  if (!isFinite(n)) return n > 0 ? "∞" : "-∞";
  return n.toExponential(3);
}

function fmtVec(v: number[]): string {
  return `[${v.map((x) => fmtSci(x)).join(", ")}]`;
}

interface Props {
  observables: Observable[];
}

export default function ObservablesPanel({ observables }: Props) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "0.8rem",
          fontFamily: "var(--font-mono)",
        }}
      >
        <thead>
          <tr style={{ borderBottom: "2px solid var(--k4-border)" }}>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>VP</th>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>
              |B| (T)
            </th>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>
              B_total
            </th>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>
              B_cut
            </th>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>
              Selectivity
            </th>
            <th style={{ textAlign: "left", padding: "0.4rem 0.5rem" }}>
              Claim
            </th>
          </tr>
        </thead>
        <tbody>
          {observables.map((obs) => (
            <tr
              key={obs.viewport_id}
              style={{ borderBottom: "1px solid var(--k4-border)" }}
            >
              <td style={{ padding: "0.4rem 0.5rem", fontWeight: 600 }}>
                {obs.viewport_id}
              </td>
              <td style={{ padding: "0.4rem 0.5rem" }}>
                {fmtSci(obs.B_magnitude)}
              </td>
              <td style={{ padding: "0.4rem 0.5rem" }}>
                {fmtVec(obs.B_total)}
              </td>
              <td style={{ padding: "0.4rem 0.5rem" }}>
                {fmtVec(obs.B_cut)}
              </td>
              <td style={{ padding: "0.4rem 0.5rem" }}>
                {fmtSci(obs.selectivity)}
              </td>
              <td style={{ padding: "0.4rem 0.5rem" }}>
                <span className={`badge badge-${obs.claim_class}`}>
                  [{obs.claim_class}]
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
