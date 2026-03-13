import type { Metadata } from "next";

export const metadata: Metadata = { title: "Updates" };

interface UpdateEntry {
  date: string;
  title: string;
  body: string;
  badge?: string;
}

const UPDATES: UpdateEntry[] = [
  {
    date: "2026-03-12",
    title: "Website launch",
    badge: "new",
    body: "k4forge.org is live. Static site built with Next.js, serving precomputed artifacts from the engine.",
  },
  {
    date: "2026-03-12",
    title: "Physical realization layer",
    badge: "engine",
    body: "Filament, bundle, and solenoid models integrated. Filament F0 matches existing pipeline at 1e-15 tolerance. 62 tests passing.",
  },
  {
    date: "2026-03-12",
    title: "Figure generation",
    badge: "engine",
    body: "Three figures per run: geometry.png, field_slice.png, probe_summary.png. Generated during k4 run and regenerable via k4 figures.",
  },
  {
    date: "2026-03-12",
    title: "Architecture hardening",
    badge: "engine",
    body: "Encoding hardening, import facade, frozen_digest in manifest, artifact round-trip tests. Phase 2 complete.",
  },
];

export default function UpdatesPage() {
  return (
    <>
      <div className="page-header">
        <h1>Updates</h1>
        <p>Project changelog and announcements.</p>
      </div>

      <section className="section">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {UPDATES.map((entry, i) => (
            <div className="card" key={i}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  marginBottom: "0.5rem",
                }}
              >
                <time
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.8rem",
                    color: "var(--k4-text-muted)",
                  }}
                >
                  {entry.date}
                </time>
                {entry.badge && (
                  <span
                    style={{
                      fontSize: "0.7rem",
                      padding: "0.1em 0.4em",
                      borderRadius: "3px",
                      background: "var(--k4-surface-2)",
                      border: "1px solid var(--k4-border)",
                      color: "var(--k4-text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {entry.badge}
                  </span>
                )}
              </div>
              <h3>{entry.title}</h3>
              <p>{entry.body}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
