import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <>
      <div className="page-header">
        <h1>About K4 Forge</h1>
        <p>
          What the project is, what it proves, and what it does not claim.
        </p>
      </div>

      <section className="section">
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          The core idea
        </h2>
        <p style={{ marginBottom: "1rem" }}>
          A complete graph on four vertices (K<sub>4</sub>) has six edges,
          three independent cycles, and three independent cuts. Driving current
          through these edges creates a magnetic field whose cycle and cut
          components are algebraically orthogonal: M<sup>T</sup>G = 0. This
          identity is unconditional &mdash; it holds for any edge lengths, any
          current pattern, any field model.
        </p>
        <p style={{ marginBottom: "1rem" }}>
          When the tetrahedron is regular and the Biot-Savart model applies,
          a stronger property emerges: the field matrix F<sub>0</sub> applied
          to the cut basis G produces zero &mdash; F<sub>0</sub>&middot;G = 0
          (theorem <strong>T3.1</strong>, independently verified as integer-exact
          via <strong>INT.CG_zero</strong>).
          This means the centroid magnetic field is entirely determined by the
          cycle currents. The cut currents generate zero net field at the
          center. Full 3D controllability follows from det(F<sub>0</sub>&middot;M) = 32
          (<strong>INT.det_CM_32</strong>), with condition number &kappa; = 2
          (<strong>INT.gram_CM</strong>).
        </p>
        <p>
          This is the foundation for exact, verifiable electromagnetic field
          control: you can specify a desired B-field at the centroid and solve
          for the unique cycle currents that produce it, with a known and
          bounded error.
        </p>
      </section>

      <section className="section">
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          Claim taxonomy
        </h2>
        <p style={{ marginBottom: "1rem" }}>
          Every result carries a claim class that says exactly how strong
          the guarantee is:
        </p>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.9rem",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "1px solid var(--k4-border)" }}>
              <th style={{ textAlign: "left", padding: "0.5rem 1rem 0.5rem 0" }}>Class</th>
              <th style={{ textAlign: "left", padding: "0.5rem 0" }}>Meaning</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["[A]", "Algebraic exact. Integer identity, unconditional.", "T0.1–T0.15, INT.*, T1.1–T1.8"],
              ["[G]", "Geometry-dependent exact. Requires regular K4 + named model.", "T2.5–T2.7, T3.1–T3.3, SYM.*"],
              ["[G*]", "Model-limited. Valid within stated regime only.", "—"],
              ["[M]", "Numerical. Never promoted without a named proof path.", "Sel.1–Sel.3"],
              ["[H]", "Heuristic. Engineering guidance, not a proof.", "—"],
              ["[C]", "Conjectural. Incomplete proof.", "—"],
            ].map(([cls, desc, theorems]) => (
              <tr key={cls} style={{ borderBottom: "1px solid var(--k4-border)" }}>
                <td
                  style={{
                    padding: "0.5rem 1rem 0.5rem 0",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 600,
                  }}
                >
                  {cls}
                </td>
                <td style={{ padding: "0.5rem 0" }}>
                  {desc}
                  {theorems !== "—" && (
                    <span style={{ display: "block", fontSize: "0.8rem", color: "var(--k4-text-muted)", marginTop: "0.15rem", fontFamily: "var(--font-mono)" }}>
                      Backed by: {theorems}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}>
          <Link href="/docs/claims/">
            Full theorem inventory and proof reference &rarr;
          </Link>
        </p>
      </section>

      <section className="section">
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          What this project does <em>not</em> claim
        </h2>
        <ul style={{ paddingLeft: "1.25rem", color: "var(--k4-text-muted)" }}>
          <li>No medical or therapeutic benefit is claimed or implied.</li>
          <li>No consumer product readiness.</li>
          <li>
            Numerical results beyond the stated claim class are unverified.
          </li>
          <li>
            Physical realization models are approximations &mdash; real hardware
            requires independent validation.
          </li>
        </ul>
      </section>

      <div className="safety-banner" style={{ marginTop: "2rem" }}>
        <strong>Research use only.</strong>{" "}
        <Link href="/safety/">Read the full safety notice.</Link>
      </div>
    </>
  );
}
