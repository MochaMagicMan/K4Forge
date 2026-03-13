import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Documentation" };

export default function DocsPage() {
  return (
    <>
      <div className="page-header">
        <h1>Documentation</h1>
        <p>Technical reference for the K4 engine.</p>
      </div>

      <section className="section">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "1rem",
          }}
        >
          <div className="card">
            <h3>Constitution</h3>
            <p>
              Architecture rules, import boundaries, and the claim taxonomy.
              The law of the codebase.
            </p>
            <p style={{ marginTop: "0.5rem" }}>
              <a
                href="https://github.com/wardc/k4-engine/blob/main/docs/CONSTITUTION.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                Read on GitHub &rarr;
              </a>
            </p>
          </div>

          <div className="card">
            <h3>Implementation Design</h3>
            <p>
              Phase-by-phase build plan: scaffold, hardening, figures,
              physical realization, and beyond.
            </p>
            <p style={{ marginTop: "0.5rem" }}>
              <a
                href="https://github.com/wardc/k4-engine/blob/main/docs/IMPLEMENTATION_DESIGN.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                Read on GitHub &rarr;
              </a>
            </p>
          </div>

          <div className="card">
            <h3>Viewport &amp; Figure Spec</h3>
            <p>
              Canonical viewport positions, C<sub>3</sub> axis definition,
              and the three standard figures generated per run.
            </p>
            <p style={{ marginTop: "0.5rem" }}>
              <a
                href="https://github.com/wardc/k4-engine/blob/main/docs/VIEWPORT_AND_FIGURE_SPEC.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                Read on GitHub &rarr;
              </a>
            </p>
          </div>

          <div className="card">
            <h3>Artifact Schema</h3>
            <p>
              JSON structure for run artifacts: manifest, spec, drive,
              observables, claim, environment.
            </p>
            <p style={{ marginTop: "0.5rem" }}>
              <Link href="/demo/">See a live artifact in the demo &rarr;</Link>
            </p>
          </div>

          <div className="card">
            <h3>CLI Reference</h3>
            <p>
              Commands: <code>k4 run</code>, <code>k4 inspect</code>,{" "}
              <code>k4 figures</code>. Preset system and artifact management.
            </p>
            <pre
              style={{
                marginTop: "0.5rem",
                fontSize: "0.8rem",
                padding: "0.5rem",
              }}
            >
{`python -m k4_cli.run run basic-bz
python -m k4_cli.run inspect <dir>
python -m k4_cli.run figures <dir>`}
            </pre>
          </div>

          <div className="card">
            <h3>Frozen Core</h3>
            <p>
              182 consistency checks in <code>k4_frozen/</code>. Truth kernel
              (M, G, D matrices), field engine, and Biot-Savart implementation.
            </p>
            <pre
              style={{
                marginTop: "0.5rem",
                fontSize: "0.8rem",
                padding: "0.5rem",
              }}
            >
              python -m k4_frozen.verify_all
            </pre>
          </div>
        </div>
      </section>
    </>
  );
}
