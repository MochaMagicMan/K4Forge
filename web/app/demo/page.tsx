"use client";

import { useEffect, useState } from "react";
import type { DemoIndex, DemoArtifact } from "@/lib/types";
import PresetSelector from "@/components/PresetSelector";
import ProvenancePanel from "@/components/ProvenancePanel";

type Tab = "target" | "solution" | "field" | "probes" | "residual" | "provenance";

const TABS: { id: Tab; label: string }[] = [
  { id: "target", label: "Target" },
  { id: "solution", label: "Solution" },
  { id: "field", label: "Field" },
  { id: "probes", label: "Probes" },
  { id: "residual", label: "Residual" },
  { id: "provenance", label: "Provenance" },
];

function fmtSci(n: number, digits = 4): string {
  if (n === 0) return "0";
  if (!isFinite(n)) return n > 0 ? "+∞" : "-∞";
  return n.toExponential(digits);
}

function fmtVec(v: number[]): string {
  return `[${v.map((x) => fmtSci(x, 2)).join(", ")}]`;
}

function fmtMicro(n: number): string {
  return (n * 1e6).toFixed(2);
}

const EDGE_LABELS = ["E01", "E02", "E03", "E12", "E13", "E23"];

/** Derive a human-readable intent label from the target vector. */
function deriveTargetIntent(B: number[]): string {
  const [bx, by, bz] = B;
  const mag = Math.sqrt(bx * bx + by * by + bz * bz);
  if (mag === 0) return "Zero field";
  const abs = [Math.abs(bx), Math.abs(by), Math.abs(bz)];
  const maxIdx = abs.indexOf(Math.max(...abs));
  const sign = B[maxIdx] > 0 ? "+" : "−";
  const axis = ["X", "Y", "Z"][maxIdx];
  const magStr = fmtMicro(mag);
  const dominant = abs[maxIdx] / mag;
  if (dominant > 0.99) {
    return `${sign}${axis} axial field, ${magStr} µT at centroid`;
  }
  return `${magStr} µT at centroid`;
}

export default function DemoPage() {
  const [index, setIndex] = useState<DemoIndex | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [artifact, setArtifact] = useState<DemoArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [activeTab, setActiveTab] = useState<Tab>("target");
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    fetch("/demo/index.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: DemoIndex) => {
        setIndex(data);
        if (data.presets.length > 0) setSelected(data.presets[0].id);
        setLoading(false);
      })
      .catch((err) => {
        setError(`Failed to load demo index: ${err.message}`);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!index || !selected) return;
    const preset = index.presets.find((p) => p.id === selected);
    if (!preset) return;
    setLoading(true);
    fetch(`/demo/${preset.artifact_path}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: DemoArtifact) => {
        setArtifact(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(`Failed to load artifact: ${err.message}`);
        setLoading(false);
      });
  }, [index, selected]);

  if (error) {
    return (
      <>
        <div className="page-header"><h1>Demo</h1></div>
        <div style={{ color: "var(--k4-red)", padding: "1rem" }}>{error}</div>
      </>
    );
  }

  const presetBase = index?.presets.find((p) => p.id === selected)
    ?.artifact_path.replace("/artifact.json", "") ?? "";

  const centroidProbe = artifact?.observables.find((o) => o.viewport_id === "VP-01");
  const B_target = artifact?.spec.control_spec.B_target ?? [0, 0, 0];
  const B_achieved = centroidProbe?.B_total ?? [0, 0, 0];
  const B_residual = B_target.map((t, i) => B_achieved[i] - t);
  const residualMag = Math.sqrt(B_residual.reduce((s, x) => s + x * x, 0));
  const targetMag = Math.sqrt(B_target.reduce((s, x) => s + x * x, 0));
  const achievedMag = Math.sqrt(B_achieved.reduce((s, x) => s + x * x, 0));
  const relError = targetMag > 0 ? (residualMag / targetMag) * 100 : 0;
  const intentLabel = deriveTargetIntent(B_target);

  return (
    <>
      <div className="page-header" style={{ paddingBottom: "1.25rem" }}>
        <h1>Demo</h1>
        <p style={{ maxWidth: "640px" }}>
          Set a field target. The engine solves for controls. Inspect the result.
        </p>
      </div>

      {index && (
        <section style={{ marginBottom: "1.25rem" }}>
          <PresetSelector presets={index.presets} selected={selected} onSelect={setSelected} />
        </section>
      )}

      {loading && (
        <div style={{ padding: "3rem", textAlign: "center", color: "var(--k4-text-muted)" }}>
          Loading...
        </div>
      )}

      {artifact && !loading && (
        <>
          {/* ── TOP STRIP ── */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr 1fr",
            gap: "0.75rem",
            marginBottom: "1.25rem",
          }}>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Control Objective</div>
              <div className="metric-value" style={{ fontSize: "0.85rem", lineHeight: 1.4 }}>
                {intentLabel}
              </div>
            </div>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Achieved</div>
              <div className="metric-value">{fmtMicro(achievedMag)} µT</div>
              <div className="metric-sub">at centroid</div>
            </div>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Match</div>
              <div className="metric-value" style={{
                color: residualMag < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
                fontSize: "1.1rem",
              }}>
                {residualMag < 1e-15 ? "Exact" : `${relError.toFixed(3)}% error`}
              </div>
              <div className="metric-sub">
                <span className={`badge badge-${centroidProbe?.claim_class ?? 'M'}`}>
                  [{centroidProbe?.claim_class ?? 'M'}]
                </span>
              </div>
            </div>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Model</div>
              <div className="metric-value" style={{ fontSize: "0.8rem" }}>
                Regular K4 · {artifact.drive.regime}
              </div>
              <div className="metric-sub">Edge-filament Biot-Savart</div>
            </div>
          </div>

          {/* ── TABS ── */}
          <div style={{
            display: "flex",
            borderBottom: "2px solid var(--k4-border)",
            marginBottom: "1rem",
            overflowX: "auto",
          }}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: "0.6rem 1.2rem",
                  background: "transparent",
                  color: activeTab === tab.id ? "var(--k4-accent)" : "var(--k4-text-muted)",
                  border: "none",
                  borderBottom: activeTab === tab.id ? "2px solid var(--k4-accent)" : "2px solid transparent",
                  marginBottom: "-2px",
                  cursor: "pointer",
                  fontSize: "0.85rem",
                  fontFamily: "var(--font-sans)",
                  fontWeight: activeTab === tab.id ? 600 : 400,
                  whiteSpace: "nowrap",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div style={{ minHeight: "400px" }}>

            {/* ═══ TARGET ═══ */}
            {activeTab === "target" && (
              <div>
                <div className="card" style={{ marginBottom: "1rem", padding: "1rem 1.25rem" }}>
                  <div style={{ fontSize: "0.7rem", color: "var(--k4-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.35rem" }}>
                    Target intent
                  </div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>
                    {intentLabel}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginTop: "0.25rem", fontFamily: "var(--font-mono)" }}>
                    B_target = {fmtVec(B_target)} T
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div className="card">
                    <h3 style={{ marginBottom: "0.75rem" }}>Control Point</h3>
                    <div className="kv-grid">
                      <span className="kv-key">Location</span>
                      <span className="kv-val">Centroid (geometric center)</span>
                      <span className="kv-key">Quantity</span>
                      <span className="kv-val">Magnetic field B</span>
                      <span className="kv-key">Direction</span>
                      <span className="kv-val">{B_target[2] !== 0 && B_target[0] === 0 && B_target[1] === 0 ? "+Z (axial)" : "Custom"}</span>
                      <span className="kv-key">Magnitude</span>
                      <span className="kv-val">{fmtMicro(targetMag)} µT</span>
                      <span className="kv-key">Regime</span>
                      <span className="kv-val">{artifact.drive.regime}</span>
                    </div>
                  </div>
                  <div className="card">
                    <h3 style={{ marginBottom: "0.75rem" }}>Model Scope</h3>
                    <div className="kv-grid">
                      <span className="kv-key">Geometry</span>
                      <span className="kv-val">Regular K4, L = {(artifact.spec.geometry_spec.edge_length * 100).toFixed(1)} cm</span>
                      <span className="kv-key">Field model</span>
                      <span className="kv-val">Biot-Savart thin-wire filament</span>
                      <span className="kv-key">Active controls</span>
                      <span className="kv-val">6 edge current amplitudes</span>
                      <span className="kv-key">Corner generators</span>
                      <span className="kv-val" style={{ color: "var(--k4-text-muted)", fontStyle: "italic" }}>Not included in this model</span>
                      <span className="kv-key">I_max</span>
                      <span className="kv-val">{artifact.spec.control_spec.I_max_per_edge} A per edge</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ═══ SOLUTION ═══ */}
            {activeTab === "solution" && (
              <div>
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.25rem" }}>Solved Edge Currents</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginBottom: "0.75rem" }}>
                    The engine chose these 6 edge current amplitudes to produce the requested field at the centroid.
                  </p>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(6, 1fr)",
                    gap: "0.5rem",
                    marginBottom: "1rem",
                  }}>
                    {artifact.drive.I_edge.map((val, i) => (
                      <div key={i} style={{
                        background: "var(--k4-surface-2)",
                        borderRadius: "6px",
                        padding: "0.6rem 0.5rem",
                        textAlign: "center",
                      }}>
                        <div style={{ fontSize: "0.7rem", color: "var(--k4-text-muted)", marginBottom: "0.25rem" }}>
                          {EDGE_LABELS[i]}
                        </div>
                        <div style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.9rem",
                          fontWeight: 600,
                          color: Math.abs(val) < 1e-10 ? "var(--k4-text-muted)" : val > 0 ? "var(--k4-green)" : "var(--k4-red)",
                        }}>
                          {Math.abs(val) < 1e-10 ? "0" : `${val > 0 ? "+" : ""}${(val * 1000).toFixed(1)}`} mA
                        </div>
                      </div>
                    ))}
                  </div>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                    gap: "0.75rem",
                  }}>
                    {[
                      ["Peak Current", `${(artifact.drive.I_max * 1000).toFixed(1)} mA`],
                      ["Power", `${(artifact.drive.P_dissipated * 1e6).toFixed(0)} µW`],
                      ["Peak Voltage", `${(artifact.drive.V_max * 1e3).toFixed(3)} mV`],
                    ].map(([label, val]) => (
                      <div key={label} style={{ background: "var(--k4-surface-2)", borderRadius: "6px", padding: "0.5rem 0.75rem" }}>
                        <div className="metric-label">{label}</div>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>{val}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.5rem" }}>Signal Model</h3>
                  <div className="kv-grid">
                    <span className="kv-key">Type</span>
                    <span className="kv-val">DC edge-current solve</span>
                    <span className="kv-key">Active controls</span>
                    <span className="kv-val">Edge current amplitudes only</span>
                    <span className="kv-key">Corner generators</span>
                    <span className="kv-val" style={{ color: "var(--k4-text-muted)", fontStyle: "italic" }}>Not included</span>
                    <span className="kv-key">Frequency / Phase</span>
                    <span className="kv-val">DC — not applicable</span>
                  </div>
                </div>

                <div className="card">
                  <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    style={{
                      background: "none", border: "none", color: "var(--k4-accent)",
                      cursor: "pointer", fontSize: "0.85rem", padding: 0, fontFamily: "var(--font-sans)",
                    }}
                  >
                    {showAdvanced ? "▾" : "▸"} Internal coordinates (cycle/cut decomposition)
                  </button>
                  {showAdvanced && (
                    <div style={{ marginTop: "0.75rem" }}>
                      <div className="kv-grid">
                        <span className="kv-key">Cycle weights w</span>
                        <span className="kv-val">[{artifact.drive.w.map((v) => v.toFixed(6)).join(", ")}]</span>
                        <span className="kv-key">Cut weights u_coil</span>
                        <span className="kv-val">[{artifact.drive.u_coil.map((v) => v.toFixed(6)).join(", ")}]</span>
                        <span className="kv-key">Vertex weights</span>
                        <span className="kv-val">[{artifact.drive.u_vertex.map((v) => v.toFixed(6)).join(", ")}]</span>
                      </div>
                      <p style={{ fontSize: "0.75rem", color: "var(--k4-text-muted)", marginTop: "0.5rem" }}>
                        The Hodge decomposition splits I_edge = M·w + G·u into cycle (divergence-free) and
                        cut (curl-free) components. For DC, only cycle weights produce field at the centroid.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ═══ FIELD ═══ */}
            {activeTab === "field" && (
              <div>
                <div style={{
                  background: "var(--k4-surface)",
                  borderRadius: "8px",
                  border: "1px solid var(--k4-border)",
                  padding: "1rem",
                  marginBottom: "1rem",
                }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between", alignItems: "baseline",
                    marginBottom: "0.75rem",
                  }}>
                    <h3 style={{ color: "var(--k4-text)", margin: 0 }}>Resulting Field</h3>
                    <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--k4-text-muted)" }}>
                      |B| · XY plane · z = 0 · <span className="badge badge-M">[M]</span>
                    </span>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <img
                      src={`/demo/${presetBase}/figures/field_slice.png`}
                      alt="Magnetic field magnitude produced by the solved edge currents, shown as a heatmap in the XY plane through the centroid"
                      style={{ maxWidth: "100%", maxHeight: "520px", borderRadius: "6px" }}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.75rem" }}>
                  {[
                    ["Slice Plane", "XY at z = 0", "Normal: +Z"],
                    ["Quantity", "|B| magnitude", "µT, log scale"],
                    ["Field Model", "Biot-Savart", "Thin-wire filament"],
                    ["Control Point", "★ Centroid", "(0, 0, 0)"],
                  ].map(([label, val, sub]) => (
                    <div key={label} className="card" style={{ padding: "0.6rem 0.75rem" }}>
                      <div className="metric-label">{label}</div>
                      <div className="metric-value" style={label === "Control Point" ? { color: "var(--k4-gold)" } : {}}>{val}</div>
                      <div className="metric-sub">{sub}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ═══ PROBES ═══ */}
            {activeTab === "probes" && (
              <div>
                <div className="card" style={{ marginBottom: "1rem", padding: "1rem 1.25rem" }}>
                  <p style={{ fontSize: "0.85rem", color: "var(--k4-text-muted)", margin: 0 }}>
                    The field is evaluated at 9 canonical positions to characterize the spatial behavior of the solution.
                    VP-01 (centroid) is the control point and carries claim <span className="badge badge-G">[G]</span> — geometry-exact
                    under regular K4. All others are numerical comparison points <span className="badge badge-M">[M]</span>.
                  </p>
                  <div style={{
                    marginTop: "0.75rem", padding: "0.5rem 0.6rem",
                    background: "var(--k4-surface-2)", borderRadius: "6px",
                    fontSize: "0.75rem",
                  }}>
                    <strong style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--k4-text-muted)" }}>
                      Why VP-01 is [G] and the rest are [M]
                    </strong>
                    <p style={{ margin: "0.25rem 0 0", color: "var(--k4-text-muted)" }}>
                      At the centroid, the field matrix factorizes exactly:
                      F<sub>0</sub>·M = &alpha;·S where S is the integer sign matrix
                      (<strong>SYM.sign</strong>). Cut annihilation F<sub>0</sub>·G = 0 is proven
                      symbolically (<strong>SYM.F0G</strong>) and to Integer(0) (<strong>INT.CG_zero</strong>).
                      Away from the centroid, no such closed form exists — those values
                      are purely numerical.
                    </p>
                  </div>
                </div>
                <div className="card">
                  <table style={{
                    width: "100%", borderCollapse: "collapse",
                    fontSize: "0.8rem", fontFamily: "var(--font-mono)",
                  }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--k4-border)" }}>
                        <th style={{ textAlign: "left", padding: "0.4rem 0.5rem", color: "var(--k4-text-muted)" }}>Probe</th>
                        <th style={{ textAlign: "right", padding: "0.4rem 0.5rem", color: "var(--k4-text-muted)" }}>|B| (µT)</th>
                        <th style={{ textAlign: "left", padding: "0.4rem 0.5rem", color: "var(--k4-text-muted)" }}>B direction</th>
                        <th style={{ textAlign: "center", padding: "0.4rem 0.5rem", color: "var(--k4-text-muted)" }}>Claim</th>
                      </tr>
                    </thead>
                    <tbody>
                      {artifact.observables.map((obs) => {
                        const isCenter = obs.viewport_id === "VP-01";
                        return (
                          <tr key={obs.viewport_id} style={{
                            borderBottom: "1px solid var(--k4-border)",
                            background: isCenter ? "rgba(255, 215, 0, 0.04)" : "transparent",
                          }}>
                            <td style={{ padding: "0.4rem 0.5rem", fontWeight: isCenter ? 600 : 400 }}>
                              {isCenter && <span style={{ color: "var(--k4-gold)", marginRight: "0.25rem" }}>★</span>}
                              {obs.viewport_id}
                            </td>
                            <td style={{ padding: "0.4rem 0.5rem", textAlign: "right" }}>
                              {(obs.B_magnitude * 1e6).toFixed(3)}
                            </td>
                            <td style={{ padding: "0.4rem 0.5rem", color: "var(--k4-text-muted)" }}>
                              {fmtVec(obs.B_total)}
                            </td>
                            <td style={{ padding: "0.4rem 0.5rem", textAlign: "center" }}>
                              <span className={`badge badge-${obs.claim_class}`}>[{obs.claim_class}]</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ═══ RESIDUAL ═══ */}
            {activeTab === "residual" && (
              <div>
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.25rem" }}>Target vs Achieved</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginBottom: "0.75rem" }}>
                    At the control point (centroid). The engine was asked to produce the target; the residual shows how close it got.
                  </p>
                  <table style={{
                    width: "100%", borderCollapse: "collapse",
                    fontSize: "0.85rem", fontFamily: "var(--font-mono)",
                  }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--k4-border)" }}>
                        <th style={{ textAlign: "left", padding: "0.5rem", width: "120px" }}></th>
                        <th style={{ textAlign: "right", padding: "0.5rem", color: "var(--k4-text-muted)" }}>Bx</th>
                        <th style={{ textAlign: "right", padding: "0.5rem", color: "var(--k4-text-muted)" }}>By</th>
                        <th style={{ textAlign: "right", padding: "0.5rem", color: "var(--k4-text-muted)" }}>Bz</th>
                        <th style={{ textAlign: "right", padding: "0.5rem", color: "var(--k4-text-muted)" }}>|B|</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: "1px solid var(--k4-border)" }}>
                        <td style={{ padding: "0.5rem", color: "var(--k4-text-muted)" }}>Target</td>
                        {B_target.map((v, i) => <td key={i} style={{ padding: "0.5rem", textAlign: "right" }}>{fmtSci(v)}</td>)}
                        <td style={{ padding: "0.5rem", textAlign: "right" }}>{fmtSci(targetMag)}</td>
                      </tr>
                      <tr style={{ borderBottom: "1px solid var(--k4-border)" }}>
                        <td style={{ padding: "0.5rem", color: "var(--k4-text-muted)" }}>Achieved</td>
                        {B_achieved.map((v, i) => <td key={i} style={{ padding: "0.5rem", textAlign: "right" }}>{fmtSci(v)}</td>)}
                        <td style={{ padding: "0.5rem", textAlign: "right" }}>{fmtSci(achievedMag)}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "0.5rem", color: "var(--k4-text-muted)", fontWeight: 600 }}>Residual ΔB</td>
                        {B_residual.map((v, i) => (
                          <td key={i} style={{
                            padding: "0.5rem", textAlign: "right", fontWeight: 600,
                            color: Math.abs(v) < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
                          }}>
                            {Math.abs(v) < 1e-15 ? "≈ 0" : fmtSci(v)}
                          </td>
                        ))}
                        <td style={{
                          padding: "0.5rem", textAlign: "right", fontWeight: 600,
                          color: residualMag < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
                        }}>
                          {residualMag < 1e-15 ? "≈ 0" : fmtSci(residualMag)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <div className="card" style={{ padding: "0.75rem 1rem", textAlign: "center" }}>
                    <div className="metric-label">Relative Error</div>
                    <div className="metric-value" style={{
                      color: relError < 0.001 ? "var(--k4-green)" : "var(--k4-gold)",
                      fontSize: "1.5rem", margin: "0.25rem 0",
                    }}>
                      {relError < 0.001 ? "< 0.001%" : `${relError.toFixed(3)}%`}
                    </div>
                    <div className="metric-sub">
                      Centroid claim: <span className={`badge badge-${centroidProbe?.claim_class ?? 'M'}`}>
                        [{centroidProbe?.claim_class ?? 'M'}]
                      </span>{" "}
                      {centroidProbe?.claim_class === "G" ? "geometry-exact" : "model-dependent"}
                    </div>
                  </div>
                  <div className="card" style={{ padding: "0.75rem 1rem" }}>
                    <div className="metric-label">Why is this exact?</div>
                    <p style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginTop: "0.25rem" }}>
                      For a regular K4 with DC edge currents, the centroid field is determined exactly by the
                      cycle-space projection. The residual is algebraically zero — a property of the graph
                      topology, not a numerical coincidence.
                    </p>
                    <div style={{
                      marginTop: "0.5rem", padding: "0.5rem 0.6rem",
                      background: "var(--k4-surface-2)", borderRadius: "6px",
                      fontSize: "0.75rem", fontFamily: "var(--font-mono)",
                    }}>
                      <div style={{ color: "var(--k4-text-muted)", marginBottom: "0.35rem", fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        Theorem backing
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.15rem 0.75rem" }}>
                        <span className="badge badge-G" style={{ fontSize: "0.65rem" }}>[A]</span>
                        <span><strong>T1.1</strong> M<sup>T</sup>G = 0 — Hodge orthogonality (cycle ⊥ cut)</span>
                        <span className="badge badge-G" style={{ fontSize: "0.65rem" }}>[A]</span>
                        <span><strong>INT.CG_zero</strong> C<sub>INT</sub>·G = 0 — cut annihilation to Integer(0)</span>
                        <span className="badge badge-G" style={{ fontSize: "0.65rem" }}>[G]</span>
                        <span><strong>T3.1</strong> F·G = 0 — cut currents produce zero field at centroid</span>
                        <span className="badge badge-G" style={{ fontSize: "0.65rem" }}>[A]</span>
                        <span><strong>INT.det_CM_32</strong> det(C<sub>INT</sub>·M) = 32 — full controllability</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ═══ PROVENANCE ═══ */}
            {activeTab === "provenance" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", alignItems: "start" }}>
                <ProvenancePanel manifest={artifact.manifest} claim={artifact.claim} />
                <div>
                  <div className="card" style={{ marginBottom: "1rem" }}>
                    <h3 style={{ marginBottom: "0.5rem" }}>Model Stack</h3>
                    <div className="kv-grid">
                      <span className="kv-key">Geometry</span>
                      <span className="kv-val">Regular K4 tetrahedron</span>
                      <span className="kv-key">Field model</span>
                      <span className="kv-val">Biot-Savart thin-wire (filament)</span>
                      <span className="kv-key">Control model</span>
                      <span className="kv-val">DC edge-current solve</span>
                      <span className="kv-key">Omissions</span>
                      <span className="kv-val" style={{ fontStyle: "italic", color: "var(--k4-text-muted)" }}>No corner generators, no AC, no mutual inductance</span>
                    </div>
                  </div>
                  <div className="card">
                    <h3 style={{ marginBottom: "0.5rem" }}>Raw Artifacts</h3>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                      {["manifest", "spec", "drive", "observables", "claim"].map((f) => (
                        <a key={f} href={`/demo/${presetBase}/${f}.json`} target="_blank" rel="noopener noreferrer"
                          style={{
                            fontFamily: "var(--font-mono)", fontSize: "0.8rem",
                            padding: "0.3rem 0.6rem", background: "var(--k4-surface-2)",
                            borderRadius: "4px", border: "1px solid var(--k4-border)",
                          }}>
                          {f}.json
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
