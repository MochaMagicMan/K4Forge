import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "K4 Forge — Tetrahedral EM Field Control",
    template: "%s | K4 Forge",
  },
  description:
    "Open-source tetrahedral electromagnetic field control engine. " +
    "Exact Hodge decomposition on K4 with verifiable provenance.",
  metadataBase: new URL("https://k4forge.org"),
};

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/about/", label: "About" },
  { href: "/demo/", label: "Demo" },
  { href: "/docs/", label: "Docs" },
  { href: "/updates/", label: "Updates" },
  { href: "/contact/", label: "Contact" },
] as const;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav
          style={{
            borderBottom: "1px solid var(--k4-border)",
            padding: "0.75rem 0",
          }}
        >
          <div
            className="container"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "0.5rem",
            }}
          >
            <Link
              href="/"
              style={{
                fontWeight: 700,
                fontSize: "1.1rem",
                color: "var(--k4-text)",
                fontFamily: "var(--font-mono)",
              }}
            >
              K4 Forge
            </Link>
            <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap" }}>
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  style={{ fontSize: "0.9rem" }}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/ja/"
                style={{
                  fontSize: "0.9rem",
                  fontWeight: 600,
                  color: "var(--k4-accent, #c8361f)",
                }}
              >
                日本語
              </Link>
              <a
                href="https://github.com/wardc-developer/k4-engine"
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: "0.9rem", color: "var(--k4-text-muted)" }}
              >
                GitHub
              </a>
            </div>
          </div>
        </nav>

        <main className="container" style={{ minHeight: "70vh" }}>
          {children}
        </main>

        <footer
          style={{
            borderTop: "1px solid var(--k4-border)",
            padding: "2rem 0",
            marginTop: "3rem",
          }}
        >
          <div
            className="container"
            style={{
              display: "flex",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "1rem",
              fontSize: "0.85rem",
              color: "var(--k4-text-muted)",
            }}
          >
            <span>K4 Forge</span>
            <span>
              <Link href="/contact/">Contact</Link>
              {" · "}
              <a
                href="https://github.com/wardc-developer/k4-engine"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
