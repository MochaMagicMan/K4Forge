"use client";

import { useEffect, useState } from "react";
import type { DemoIndex, DemoArtifact } from "@/lib/types";
import Link from "next/link";
import ProvenancePanel from "@/components/ProvenancePanel";

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

/** Derive a short human-readable title from the target vector. */
function deriveTitle(B: number[]): string {
  const [bx, by, bz] = B;
  const mag = Math.sqrt(bx * bx + by * by + bz * bz);
  if (mag === 0) return "Zero field";
  const abs = [Math.abs(bx), Math.abs(by), Math.abs(bz)];
  const maxIdx = abs.indexOf(Math.max(...abs));
  const sign = B[maxIdx] > 0 ? "+" : "−";
  const axis = ["X", "Y", "Z"][maxIdx];
  const dominant = abs[maxIdx] / mag;
  if (dominant > 0.99) return `Centered ${sign}${axis} field`;
  return "Custom field target";
}

export default function DemoPage() {
  const [index, setIndex] = useState<DemoIndex | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [artifact, setArtifact] = useState<DemoArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showTechnical, setShowTechnical] = useState(false);

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
  const title = deriveTitle(B_target);
  const edgeLen = artifact?.spec.geometry_spec.edge_length ?? 0.1;

  // Multiple presets: show selector only if > 1
  const showSelector = (index?.presets.length ?? 0) > 1;

  return (
    <>
      {/* ── HEADER ── */}
      <div className="page-header" style={{ paddingBottom: "1.25rem" }}>
        <h1>{loading ? "Demo" : title}</h1>
        {artifact && !loading && (
          <p style={{ maxWidth: "640px" }}>
            The engine was asked to create a {fmtMicro(targetMag)} µT magnetic field
            {B_target[2] !== 0 && B_target[0] === 0 && B_target[1] === 0
              ? " pointing upward"
              : ""}{" "}
            at the tetrahedron&apos;s center. It solved the six edge-current amplitudes
            required to produce that result.
          </p>
        )}
        {loading && (
          <p style={{ color: "var(--k4-text-muted)" }}>Loading...</p>
        )}
      </div>

      {showSelector && index && (
        <section style={{ marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {index.presets.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelected(p.id)}
                style={{
                  padding: "0.5rem 1rem",
                  borderRadius: "6px",
                  border: p.id === selected
                    ? "2px solid var(--k4-accent)"
                    : "1px solid var(--k4-border)",
                  background: p.id === selected ? "var(--k4-accent-dim)" : "var(--k4-surface)",
                  color: "var(--k4-text)",
                  cursor: "pointer",
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.85rem",
                }}
              >
                {p.name}
              </button>
            ))}
          </div>
        </section>
      )}

      {artifact && !loading && (
        <>
          {/* ── SUMMARY STRIP ── */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "0.75rem",
            marginBottom: "1.5rem",
          }}>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Goal</div>
              <div className="metric-value">{fmtMicro(targetMag)} µT at center</div>
              <div className="metric-sub">
                {B_target[2] !== 0 && B_target[0] === 0 && B_target[1] === 0 ? "+Z axial" : "Custom direction"}
              </div>
            </div>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Result</div>
              <div className="metric-value" style={{
                color: residualMag < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
              }}>
                {residualMag < 1e-15 ? "Exact match" : `${relError.toFixed(3)}% error`}
              </div>
              <div className="metric-sub">at control point</div>
            </div>
            <div className="card" style={{ padding: "0.75rem 1rem" }}>
              <div className="metric-label">Method</div>
              <div className="metric-value" style={{ fontSize: "0.8rem" }}>
                DC edge-current solve
              </div>
              <div className="metric-sub">Regular tetrahedron, L = {(edgeLen * 100).toFixed(0)} cm</div>
            </div>
          </div>

          {/* ═══ SECTION A: REQUEST ═══ */}
          <div className="card" style={{ marginBottom: "1rem", padding: "1rem 1.25rem" }}>
            <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Requested field</h2>
            <p style={{ fontSize: "0.9rem", color: "var(--k4-text-muted)", margin: 0 }}>
              Create a {fmtMicro(targetMag)} µT
              {B_target[2] !== 0 && B_target[0] === 0 && B_target[1] === 0
                ? " upward (+Z)"
                : ""}{" "}
              magnetic field at the geometric center of a regular tetrahedron
              with {(edgeLen * 100).toFixed(0)} cm edges,
              using DC currents through the six edges.
            </p>
          </div>

          {/* ═══ SECTION B: SOLVED CONTROLS ═══ */}
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1rem", marginBottom: "0.25rem" }}>Solved controls</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--k4-text-muted)", marginBottom: "0.75rem" }}>
              These are the six edge-current amplitudes the engine solved for.
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
                ["Peak current", `${(artifact.drive.I_max * 1000).toFixed(1)} mA`],
                ["Power", `${(artifact.drive.P_dissipated * 1e6).toFixed(0)} µW`],
                ["Peak voltage", `${(artifact.drive.V_max * 1e3).toFixed(3)} mV`],
              ].map(([label, val]) => (
                <div key={label} style={{ background: "var(--k4-surface-2)", borderRadius: "6px", padding: "0.5rem 0.75rem" }}>
                  <div className="metric-label">{label}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ═══ SECTION C: RESULTING FIELD ═══ */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Resulting field</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--k4-text-muted)", marginBottom: "0.75rem" }}>
              Magnetic field magnitude in the XY plane through the center.
            </p>
            <div style={{ textAlign: "center" }}>
              <img
                src={`/demo/${presetBase}/figures/field_slice.png`}
                alt="Magnetic field magnitude produced by the solved edge currents, shown as a heatmap in the XY plane through the centroid"
                style={{ maxWidth: "100%", maxHeight: "520px", borderRadius: "6px" }}
              />
            </div>
          </div>

          {/* ── CONTEXT LINE ── */}
          <p style={{
            fontSize: "0.9rem",
            color: "var(--k4-text-muted)",
            marginBottom: "1.5rem",
            maxWidth: "640px",
          }}>
            This is an early example of <em>field sculpting</em>: specifying a desired
            field behavior, solving for control currents, and inspecting the resulting
            spatial field. The match at the center is exact under this geometry &mdash; a
            property of the{" "}
            <Link href="/docs/claims/">underlying mathematics</Link>,
            not a numerical coincidence.
          </p>

          {/* ═══ TECHNICAL DETAILS (collapsed) ═══ */}
          <div style={{ borderTop: "1px solid var(--k4-border)", paddingTop: "1rem" }}>
            <button
              onClick={() => setShowTechnical(!showTechnical)}
              style={{
                background: "none",
                border: "none",
                color: "var(--k4-accent)",
                cursor: "pointer",
                fontSize: "0.9rem",
                padding: 0,
                fontFamily: "var(--font-sans)",
                fontWeight: 500,
              }}
            >
              {showTechnical ? "▾ Hide" : "▸ Show"} technical details
            </button>

            {showTechnical && (
              <div style={{ marginTop: "1.25rem" }}>

                {/* ── Residual ── */}
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.25rem" }}>Target vs Achieved</h3>
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
                        <td style={{ padding: "0.5rem", color: "var(--k4-text-muted)", fontWeight: 600 }}>Residual</td>
                        {B_residual.map((v, i) => (
                          <td key={i} style={{
                            padding: "0.5rem", textAlign: "right", fontWeight: 600,
                            color: Math.abs(v) < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
                          }}>
                            {Math.abs(v) < 1e-15 ? "0" : fmtSci(v)}
                          </td>
                        ))}
                        <td style={{
                          padding: "0.5rem", textAlign: "right", fontWeight: 600,
                          color: residualMag < 1e-15 ? "var(--k4-green)" : "var(--k4-gold)",
                        }}>
                          {residualMag < 1e-15 ? "0" : fmtSci(residualMag)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* ── Probes ── */}
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.5rem" }}>Field probes (9 viewports)</h3>
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

                {/* ── Cycle/cut decomposition ── */}
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.5rem" }}>Internal coordinates</h3>
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

                {/* ── Theorem backing ── */}
                <div className="card" style={{ marginBottom: "1rem" }}>
                  <h3 style={{ marginBottom: "0.5rem" }}>Theorem backing</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginBottom: "0.5rem" }}>
                    The exact match at the centroid is not numerical luck. It follows from these proven identities:
                  </p>
                  <div style={{
                    fontSize: "0.8rem", fontFamily: "var(--font-mono)",
                    display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.2rem 0.75rem",
                  }}>
                    <span className="badge badge-A" style={{ fontSize: "0.65rem" }}>[A]</span>
                    <span><strong>T1.1</strong> M<sup>T</sup>G = 0 &mdash; Hodge orthogonality</span>
                    <span className="badge badge-A" style={{ fontSize: "0.65rem" }}>[A]</span>
                    <span><strong>INT.CG_zero</strong> C<sub>INT</sub>&middot;G = 0 &mdash; integer cut annihilation</span>
                    <span className="badge badge-G" style={{ fontSize: "0.65rem" }}>[G]</span>
                    <span><strong>T3.1</strong> F&middot;G = 0 &mdash; zero field from cut currents</span>
                    <span className="badge badge-A" style={{ fontSize: "0.65rem" }}>[A]</span>
                    <span><strong>INT.det_CM_32</strong> det = 32 &mdash; full controllability</span>
                  </div>
                  <p style={{ fontSize: "0.8rem", color: "var(--k4-text-muted)", marginTop: "0.5rem" }}>
                    <Link href="/docs/claims/">Full claims &amp; theorem reference &rarr;</Link>
                  </p>
                </div>

                {/* ── Provenance ── */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", alignItems: "start" }}>
                  <ProvenancePanel manifest={artifact.manifest} claim={artifact.claim} />
                  <div className="card">
                    <h3 style={{ marginBottom: "0.5rem" }}>Raw artifacts</h3>
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
