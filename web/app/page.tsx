import Link from "next/link";

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section style={{ padding: "4rem 0 3rem", textAlign: "center" }}>
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: 800,
            lineHeight: 1.2,
            marginBottom: "1rem",
          }}
        >
          Tetrahedral EM
          <br />
          Field Control
        </h1>
        <p
          style={{
            color: "var(--k4-text-muted)",
            fontSize: "1.15rem",
            maxWidth: "640px",
            margin: "0 auto 2rem",
          }}
        >
          Define a target field behavior, solve for control currents, inspect the
          resulting field, and compare target to achieved output. Every result
          carries machine-verifiable provenance.
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          <Link
            href="/demo/"
            style={{
              background: "var(--k4-accent)",
              color: "#fff",
              padding: "0.7rem 1.5rem",
              borderRadius: "6px",
              fontWeight: 600,
              fontSize: "0.95rem",
            }}
          >
            Interactive Demo
          </Link>
          <a
            href="https://github.com/wardc-developer/k4-engine"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: "var(--k4-surface)",
              color: "var(--k4-text)",
              padding: "0.7rem 1.5rem",
              borderRadius: "6px",
              fontWeight: 600,
              fontSize: "0.95rem",
              border: "1px solid var(--k4-border)",
            }}
          >
            View Source
          </a>
        </div>
      </section>

      {/* What you can inspect */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1rem",
          padding: "2rem 0",
        }}
      >
        <div className="card">
          <h3>Exact Control Basis</h3>
          <p>
            The Hodge decomposition on K<sub>4</sub> gives an exact orthogonal
            split of edge currents into cycle and cut components. The identity
            M<sup>T</sup>G = 0 is a graph property, not an approximation.
          </p>
        </div>
        <div className="card">
          <h3>Explicit Field Model</h3>
          <p>
            Every run states its geometry, field model, control variables, and
            what is <em>not</em> included. No hidden assumptions.
          </p>
        </div>
        <div className="card">
          <h3>Reproducible Artifacts</h3>
          <p>
            Each result carries a claim class, frozen-core digest, solver
            version, and numerical tolerances. Self-describing JSON you can
            inspect and verify.
          </p>
        </div>
        <div className="card">
          <h3>Target → Solve → Inspect</h3>
          <p>
            Set a target field at the centroid. The engine solves for edge
            currents. Compare the achieved field against the target and examine
            the residual.
          </p>
        </div>
      </section>
    </>
  );
}
