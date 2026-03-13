"use client";

import type { Manifest, ClaimRecord } from "@/lib/types";

interface Props {
  manifest: Manifest;
  claim: ClaimRecord;
}

export default function ProvenancePanel({ manifest, claim }: Props) {
  const rows: [string, string][] = [
    ["Preset", manifest.name],
    ["Run ID", manifest.run_id],
    ["Claim class", `[${manifest.claim_class}]`],
    ["Regime", manifest.regime],
    ["Frozen version", manifest.frozen_version],
    ["Frozen digest", manifest.frozen_digest || "n/a"],
    ["Code digest", manifest.code_digest],
    ["Schema version", manifest.artifact_schema_version],
    ["Timestamp", manifest.timestamp],
    ["Assumptions", claim.assumptions.join(", ")],
  ];

  // Add numerical tolerances
  for (const [key, val] of Object.entries(claim.numerical_tolerances)) {
    rows.push([`tol:${key}`, String(val)]);
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: "0.75rem" }}>Provenance</h3>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "0.8rem",
        }}
      >
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label} style={{ borderBottom: "1px solid var(--k4-border)" }}>
              <td
                style={{
                  padding: "0.35rem 0.75rem 0.35rem 0",
                  color: "var(--k4-text-muted)",
                  whiteSpace: "nowrap",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                }}
              >
                {label}
              </td>
              <td
                style={{
                  padding: "0.35rem 0",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                  wordBreak: "break-all",
                }}
              >
                {value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
