"use client";

import type { Drive } from "@/lib/types";

function fmtSci(n: number): string {
  if (!isFinite(n)) return n > 0 ? "+Inf" : "-Inf";
  return n.toExponential(4);
}

const EDGE_LABELS = ["E01", "E02", "E03", "E12", "E13", "E23"];

interface Props {
  drive: Drive;
}

export default function DrivePanel({ drive }: Props) {
  return (
    <div className="card">
      <h3 style={{ marginBottom: "0.75rem" }}>Drive Solution</h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--k4-text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Cycle weights w
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            [{drive.w.map((v) => v.toFixed(6)).join(", ")}]
          </div>
        </div>
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--k4-text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            I_max
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            {fmtSci(drive.I_max)} A
          </div>
        </div>
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--k4-text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            P_dissipated
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            {fmtSci(drive.P_dissipated)} W
          </div>
        </div>
      </div>

      <div
        style={{
          fontSize: "0.7rem",
          color: "var(--k4-text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: "0.35rem",
        }}
      >
        Edge currents I_edge (A)
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: "0.25rem",
        }}
      >
        {drive.I_edge.map((val, i) => (
          <div
            key={i}
            style={{
              background: "var(--k4-surface-2)",
              borderRadius: "4px",
              padding: "0.35rem",
              textAlign: "center",
              fontSize: "0.75rem",
              fontFamily: "var(--font-mono)",
            }}
          >
            <div style={{ fontSize: "0.65rem", color: "var(--k4-text-muted)" }}>
              {EDGE_LABELS[i]}
            </div>
            {val.toFixed(4)}
          </div>
        ))}
      </div>
    </div>
  );
}
