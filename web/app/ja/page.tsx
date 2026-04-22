import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "日本GO!",
  description: "Japanese learning games — Kana Rain, Count, and Pair",
};

const GAMES = [
  {
    id: "count",
    kanji: "数",
    label: "Count",
    sub: "かぞえる",
    href: null as string | null,
    description: "Practice counting in Japanese with interactive number challenges.",
  },
  {
    id: "rain",
    kanji: "雨",
    label: "Rain",
    sub: "あめ",
    href: "/ja/rain/",
    description:
      "Type the romaji of falling kana before they hit the ground. " +
      "Chain combos, unlock dakuten and digraphs, pick your theme.",
  },
  {
    id: "pair",
    kanji: "対",
    label: "Pair",
    sub: "つい",
    href: null as string | null,
    description: "Match kana to their romaji counterparts in a memory game.",
  },
] as const;

export default function JaPage() {
  return (
    <section style={{ padding: "3rem 0" }}>
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <h1
          style={{
            fontSize: "2.8rem",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: "0.5rem",
          }}
        >
          日本<span style={{ color: "var(--k4-accent)" }}>GO!</span>
        </h1>
        <p
          style={{
            color: "var(--k4-text-muted)",
            fontSize: "1rem",
            letterSpacing: "0.15em",
          }}
        >
          Japanese learning games
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1.25rem",
          maxWidth: "860px",
          margin: "0 auto",
        }}
      >
        {GAMES.map((g) => {
          const available = g.href !== null;
          const inner = (
            <div
              className="card"
              style={{
                textAlign: "center",
                padding: "2rem 1.5rem",
                opacity: available ? 1 : 0.5,
                cursor: available ? "pointer" : "default",
                transition: "transform 0.15s, box-shadow 0.15s",
              }}
            >
              <div
                style={{
                  fontSize: "3rem",
                  lineHeight: 1,
                  marginBottom: "0.5rem",
                }}
              >
                {g.kanji}
              </div>
              <h3 style={{ marginBottom: "0.25rem" }}>
                {g.label}{" "}
                <span
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--k4-text-muted)",
                  }}
                >
                  {g.sub}
                </span>
              </h3>
              <p style={{ fontSize: "0.9rem", color: "var(--k4-text-muted)" }}>
                {g.description}
              </p>
              {!available && (
                <span
                  style={{
                    display: "inline-block",
                    marginTop: "0.75rem",
                    fontSize: "0.8rem",
                    color: "var(--k4-text-muted)",
                    border: "1px solid var(--k4-border)",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "4px",
                  }}
                >
                  Coming soon
                </span>
              )}
            </div>
          );

          if (available) {
            return (
              <a
                key={g.id}
                href={g.href!}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                {inner}
              </a>
            );
          }
          return <div key={g.id}>{inner}</div>;
        })}
      </div>
    </section>
  );
}
