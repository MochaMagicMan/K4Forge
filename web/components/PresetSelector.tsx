"use client";

import type { PresetSummary } from "@/lib/types";

interface Props {
  presets: PresetSummary[];
  selected: string;
  onSelect: (id: string) => void;
}

export default function PresetSelector({ presets, selected, onSelect }: Props) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
      {presets.map((p) => (
        <button
          key={p.id}
          onClick={() => onSelect(p.id)}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            border:
              p.id === selected
                ? "2px solid var(--k4-accent)"
                : "1px solid var(--k4-border)",
            background:
              p.id === selected ? "var(--k4-accent-dim)" : "var(--k4-surface)",
            color: "var(--k4-text)",
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            fontSize: "0.85rem",
          }}
        >
          {p.name}
          <span
            className={`badge badge-${p.claim_class}`}
            style={{ marginLeft: "0.5rem" }}
          >
            [{p.claim_class}]
          </span>
        </button>
      ))}
    </div>
  );
}
