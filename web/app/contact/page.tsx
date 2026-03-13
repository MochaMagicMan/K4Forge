import type { Metadata } from "next";

export const metadata: Metadata = { title: "Contact" };

export default function ContactPage() {
  return (
    <>
      <div className="page-header">
        <h1>Contact</h1>
        <p>Get in touch with the K4 Forge project.</p>
      </div>

      <section className="section">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          <div className="card">
            <h3>GitHub Issues</h3>
            <p>
              Bug reports, feature requests, and technical discussion happen on
              the{" "}
              <a
                href="https://github.com/wardc/k4-engine/issues"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub issue tracker
              </a>
              .
            </p>
          </div>
          <div className="card">
            <h3>Email</h3>
            <p>
              For questions that don&apos;t fit a public issue:{" "}
              <a href="mailto:hello@k4forge.org">hello@k4forge.org</a>
            </p>
          </div>
          <div className="card">
            <h3>Contributing</h3>
            <p>
              Pull requests welcome. See the{" "}
              <a
                href="https://github.com/wardc/k4-engine"
                target="_blank"
                rel="noopener noreferrer"
              >
                repository
              </a>{" "}
              for contribution guidelines.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
