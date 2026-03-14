import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Claims & Theorems" };

const TIERS = [
  {
    tier: "T0",
    name: "Integer Exact (DEC & Spectral)",
    claim: "A",
    theorems: [
      ["T0.1", "L0 = 4I\u2084 \u2212 J\u2084", "Vertex Laplacian spectral decomposition"],
      ["T0.2", "C\u1D40 D\u1D40 = 0", "DEC chain exactness"],
      ["T0.3", "L1 = 4I\u2086", "Edge Laplacian is scalar identity"],
      ["T0.4", "D M = 0", "Boundary operator kills cycles"],
      ["T0.6", "D C\u1D40_T = 0", "Boundary of face = 0"],
      ["T0.7", "C\u1D40 D\u1D40 = 0", "Transpose DEC chain"],
      ["T0.8", "D_red\u1D40 = G", "Reduced incidence = cut basis"],
      ["T0.12", "M\u1D40(\u0394\u2212 2I)G = 0", "Hodge-Sigma orthogonality"],
      ["T0.14", "M\u1D40 A_opp G = rank-1", "Opposite-edge coupling structure"],
      ["T0.15", "\u2016M\u1D40 A_opp G\u2016\u00B2_F = 9", "Frobenius norm of opposite coupling"],
    ],
  },
  {
    tier: "INT",
    name: "Integer Field Structure",
    claim: "A",
    theorems: [
      ["INT.C", "C_INT \u2208 {-1,0,+1}\u00B3\u02E3\u2076", "Cross-product field matrix is integer"],
      ["INT.CM_eq_neg2S", "C_INT\u00B7M = \u22122S", "Field-cycle product is twice sign matrix"],
      ["INT.CG_zero", "C_INT\u00B7G = 0", "Cut annihilation to Integer(0)"],
      ["INT.det_CM_32", "det(C_INT\u00B7M) = 32", "Controllability determinant"],
      ["INT.gram_CM", "(C_INT\u00B7M)\u1D40(C_INT\u00B7M) = 4\u00B7Gram", "Controllability Gram, \u03BA=2"],
      ["INT.STS_gram", "S\u1D40S = Gram", "Sign matrix squared is 4I\u2212J"],
      ["INT.isotropy", "S\u00B7adj\u00B7S\u1D40 = 16I", "Centroid isotropy via adjugate"],
      ["INT.adj_check", "Gram\u00B7adj = 16I", "Adjugate correctness"],
    ],
  },
  {
    tier: "T1",
    name: "Algebraic Exact (Topology)",
    claim: "A",
    theorems: [
      ["T1.1", "M\u1D40G = 0", "Hodge orthogonality \u2014 cycle \u22A5 cut"],
      ["T1.2", "D M = 0", "Kirchhoff compatibility"],
      ["T1.3", "M\u1D40M = G\u1D40G = 4I\u2212J", "Gram identity"],
      ["T1.4", "det(M\u1D40M) = 16", "Gram determinant"],
      ["T1.5", "det([M|G]) = \u00B116", "Full-space determinant"],
      ["T1.6", "M\u207AG = G\u207AM = 0", "Pseudoinverse orthogonality"],
      ["T1.7", "P_cyc + P_cut = I\u2086", "Projector completeness"],
      ["T1.8", "P_cyc\u00B7P_cut = 0", "Projector orthogonality"],
    ],
  },
  {
    tier: "T2",
    name: "Closed-form (Inductance & Ring-quiet)",
    claim: "G",
    theorems: [
      ["T2.1", "det(G_ring) = 0", "Ring solvability condition"],
      ["T2.2", "null(G_ring) = span{1,1,1}", "Ring null space is uniform"],
      ["T2.3", "Ring-quiet \u21D4 J1+J2+J3=0", "Balanced cycle condition"],
      ["T2.5", "M_opp = 0", "Opposite edges have zero mutual inductance"],
      ["T2.6", "M\u1D40 L G = 0", "Hodge-inductance decoupling"],
      ["T2.7", "L eigenvalue degeneracy", "3-fold degenerate cycle and cut eigenvalues"],
    ],
  },
  {
    tier: "T3 / SYM",
    name: "Parametric (Electromagnetics)",
    claim: "G",
    theorems: [
      ["T3.1", "F\u00B7G = 0", "Cut annihilation at centroid (Biot-Savart)"],
      ["T3.2", "det(F\u00B7M) \u2260 0", "Controllability determinant nonzero"],
      ["T3.3", "rank(F\u00B7M) = 3", "Full 3D B-field control"],
      ["SYM.F0G", "F\u2080\u00B7G = 0", "Symbolic cut annihilation (parametric in L)"],
      ["SYM.sign", "F\u2080\u00B7M = \u03B1\u00B7S", "Field-cycle factorization"],
      ["SYM.F0M", "det(F\u2080\u00B7M), \u03BA=2", "Condition number of field matrix"],
    ],
  },
  {
    tier: "Sel",
    name: "Selection Rules (Multipole)",
    claim: "M",
    theorems: [
      ["Sel.1", "Cut dipole = 0", "Cut currents produce zero dipole moment"],
      ["Sel.2", "Cut quadrupole = 0", "Cut currents produce zero quadrupole moment"],
      ["Sel.3", "Cycle octupole = 0", "Cycle currents produce zero octupole moment"],
    ],
  },
];

const BADGE_LABELS: Record<string, string> = {
  A: "Algebraic exact",
  G: "Geometry-dependent exact",
  M: "Numerical",
};

export default function ClaimsPage() {
  return (
    <>
      <div className="page-header">
        <h1>Claims &amp; Theorems</h1>
        <p>
          What K4 Forge proves, how strong each guarantee is, and where the
          proofs live.
        </p>
      </div>

      {/* ── CLAIM TAXONOMY ── */}
      <section className="section">
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          Claim classes
        </h2>
        <p style={{ marginBottom: "1rem", color: "var(--k4-text-muted)" }}>
          Every result in K4 Forge carries a claim class that says exactly how
          strong the guarantee is. These labels appear throughout the{" "}
          <Link href="/demo/">demo</Link> and in all run artifacts.
        </p>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.9rem",
            marginBottom: "1.5rem",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "2px solid var(--k4-border)" }}>
              <th style={{ textAlign: "left", padding: "0.5rem 1rem 0.5rem 0", width: "80px" }}>Class</th>
              <th style={{ textAlign: "left", padding: "0.5rem 0" }}>Meaning</th>
              <th style={{ textAlign: "left", padding: "0.5rem 0 0.5rem 1rem" }}>Proof requirement</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["A", "Algebraic exact", "Integer identity via SymPy, unconditional", "Evaluates to Integer(0). No geometry, no model, no tolerance."],
              ["G", "Geometry-dependent exact", "Requires regular K4 + named field model", "Closed-form derivation with explicit assumptions stated."],
              ["G*", "Model-limited", "Valid within stated regime only", "Same as [G] but with additional regime constraints."],
              ["M", "Numerical", "Never promoted without a named proof path", "Verified to stated tolerance. Not a proof \u2014 a measurement."],
              ["H", "Heuristic", "Engineering guidance, not a proof", "Experience-based. No formal guarantee."],
              ["C", "Conjectural", "Incomplete proof", "Evidence exists but proof chain is not closed."],
            ].map(([cls, label, meaning, requirement]) => (
              <tr key={cls} style={{ borderBottom: "1px solid var(--k4-border)" }}>
                <td style={{ padding: "0.5rem 1rem 0.5rem 0", verticalAlign: "top" }}>
                  <span className={`badge badge-${cls}`}>[{cls}]</span>
                </td>
                <td style={{ padding: "0.5rem 0", verticalAlign: "top" }}>
                  <strong>{label}.</strong>{" "}
                  <span style={{ color: "var(--k4-text-muted)" }}>{meaning}</span>
                </td>
                <td style={{ padding: "0.5rem 0 0.5rem 1rem", fontSize: "0.8rem", color: "var(--k4-text-muted)", verticalAlign: "top" }}>
                  {requirement}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── AUTHORITATIVE vs EXPLORATORY ── */}
      <section className="section" style={{ paddingTop: 0 }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          Authoritative vs Exploratory
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
            marginBottom: "1rem",
          }}
        >
          <div className="card">
            <h3 style={{ color: "var(--k4-green)" }}>
              k4_frozen &mdash; Authoritative
            </h3>
            <p style={{ marginTop: "0.5rem" }}>
              Immutable algebraic core. 182 consistency checks. Contains the
              truth kernel (M, G, D, C_INT, S matrices), field engine, and
              Biot-Savart implementation. Never edited without a version bump
              and full audit.
            </p>
            <p style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              <strong>If k4_frozen and k4_theory disagree, k4_frozen wins.</strong>
            </p>
          </div>
          <div className="card">
            <h3 style={{ color: "var(--k4-claim-A)" }}>
              k4_theory &mdash; Exploratory Oracle
            </h3>
            <p style={{ marginTop: "0.5rem" }}>
              Independent theorem mining and proof engine. 47 registered theorems,
              S<sub>4</sub> symmetry miner, candidate discovery. Uses only numpy,
              sympy, and stdlib &mdash; never imports from k4_frozen.
            </p>
            <p style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              Cross-validated against k4_frozen in tests. The disagreement itself
              is valuable &mdash; it means something needs investigation.
            </p>
          </div>
        </div>
        <div className="card" style={{ padding: "0.75rem 1rem" }}>
          <strong style={{ fontSize: "0.85rem" }}>Promotion path:</strong>
          <span style={{ fontSize: "0.85rem", color: "var(--k4-text-muted)", marginLeft: "0.5rem" }}>
            A theorem proven in k4_theory at tier T0 (integer-exact) can be promoted
            to a <code>verify_layer1()</code> check in k4_frozen after independent
            review and explicit version bump.
          </span>
        </div>
      </section>

      {/* ── THEOREM INVENTORY ── */}
      <section className="section" style={{ paddingTop: 0 }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          Theorem inventory
        </h2>
        <p style={{ marginBottom: "1rem", color: "var(--k4-text-muted)" }}>
          47 registered theorems across 6 tiers. Each theorem is machine-verified
          on every test run.
        </p>

        {TIERS.map((group) => (
          <div key={group.tier} style={{ marginBottom: "1.5rem" }}>
            <div style={{
              display: "flex", alignItems: "baseline", gap: "0.75rem",
              marginBottom: "0.5rem",
            }}>
              <h3 style={{ fontSize: "1rem", margin: 0 }}>{group.tier}</h3>
              <span style={{ fontSize: "0.85rem", color: "var(--k4-text-muted)" }}>
                {group.name}
              </span>
              <span className={`badge badge-${group.claim}`} style={{ fontSize: "0.7rem" }}>
                [{group.claim}] {BADGE_LABELS[group.claim]}
              </span>
            </div>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.8rem",
                fontFamily: "var(--font-mono)",
              }}
            >
              <tbody>
                {group.theorems.map(([id, statement, description]) => (
                  <tr key={id} style={{ borderBottom: "1px solid var(--k4-border)" }}>
                    <td style={{
                      padding: "0.35rem 0.75rem 0.35rem 0",
                      whiteSpace: "nowrap",
                      fontWeight: 600,
                      width: "140px",
                    }}>
                      {id}
                    </td>
                    <td style={{ padding: "0.35rem 0.75rem 0.35rem 0" }}>
                      {statement}
                    </td>
                    <td style={{
                      padding: "0.35rem 0",
                      color: "var(--k4-text-muted)",
                      fontFamily: "var(--font-sans)",
                    }}>
                      {description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </section>

      {/* ── ANCHOR THEOREMS ── */}
      <section className="section" style={{ paddingTop: 0 }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
          Anchor theorems
        </h2>
        <p style={{ marginBottom: "1rem", color: "var(--k4-text-muted)" }}>
          These four theorems form the backbone of the K4 field control story.
          Together they prove: cut currents cannot produce field at the centroid,
          cycle currents give full 3D control, and the system is well-conditioned.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "1rem",
          }}
        >
          {[
            {
              id: "T1.1",
              badge: "A",
              title: "Hodge orthogonality",
              stmt: "M\u1D40G = 0",
              why: "Cycle and cut spaces are algebraically orthogonal. This is unconditional \u2014 it holds for any K4, any geometry, any field model.",
            },
            {
              id: "INT.CG_zero",
              badge: "A",
              title: "Integer cut annihilation",
              stmt: "C_INT\u00B7G = 0",
              why: "The cross-product field matrix applied to cut currents is exactly zero \u2014 verified to Integer(0) via SymPy. No Biot-Savart needed.",
            },
            {
              id: "INT.det_CM_32",
              badge: "A",
              title: "Controllability",
              stmt: "det(C_INT\u00B7M) = 32",
              why: "The field-cycle product has full rank with integer determinant 32. Three cycle currents control all three field components.",
            },
            {
              id: "INT.gram_CM",
              badge: "A",
              title: "Condition number \u03BA = 2",
              stmt: "(C_INT\u00B7M)\u1D40(C_INT\u00B7M) = 4\u00B7Gram",
              why: "The controllability Gram matrix has condition number 2 \u2014 well-conditioned by construction, not by luck.",
            },
          ].map((t) => (
            <div key={t.id} className="card">
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginBottom: "0.25rem" }}>
                <span className={`badge badge-${t.badge}`} style={{ fontSize: "0.65rem" }}>[{t.badge}]</span>
                <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>{t.id}</strong>
              </div>
              <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                {t.title}
              </div>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: "0.8rem",
                color: "var(--k4-accent)", marginBottom: "0.5rem",
              }}>
                {t.stmt}
              </div>
              <p style={{ fontSize: "0.8rem" }}>{t.why}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="safety-banner" style={{ marginTop: "1rem" }}>
        <strong>All theorems are machine-verified on every test run.</strong>{" "}
        Run <code>python -m k4_theory --prove</code> or{" "}
        <code>pytest tests/test_theory_miner.py -v</code> to verify locally.
      </div>
    </>
  );
}
