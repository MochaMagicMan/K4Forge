/**
 * Frontend JSON contract for precomputed artifacts.
 *
 * These types mirror the engine's artifact schema but are
 * the frontend's own contract — no Python imports.
 */

export interface DemoIndex {
  presets: PresetSummary[];
  generated: string; // ISO timestamp
  engine_version: string;
}

export interface PresetSummary {
  id: string;           // e.g. "basic-bz"
  name: string;         // e.g. "BASIC_BZ"
  description: string;
  claim_class: string;  // "G" | "M" | "H"
  artifact_path: string; // relative path under /demo/
}

export interface DemoArtifact {
  manifest: Manifest;
  spec: Spec;
  drive: Drive;
  observables: Observable[];
  claim: ClaimRecord;
}

export interface Manifest {
  run_id: string;
  name: string;
  description: string;
  timestamp: string;
  frozen_version: string;
  frozen_digest: string;
  code_digest: string;
  claim_class: string;
  regime: string;
  artifact_schema_version: string;
  files: string[];
  figures?: string[];
}

export interface Spec {
  control_spec: {
    B_target: number[];
    E_target: number[];
    minimize_current: boolean;
    I_max_per_edge: number;
    V_max_per_vertex: number;
    frequency: number;
    config_id: string;
  };
  geometry_spec: {
    vertices: number[][];
    edge_length: number;
    symmetry_class: string;
    wire_radius: number;
    config_id: string;
  };
}

export interface Drive {
  w: number[];
  u_coil: number[];
  u_vertex: number[];
  I_edge: number[];
  V_drive: number[];
  P_dissipated: number;
  P_reactive: number;
  I_max: number;
  V_max: number;
  frequency: number;
  regime: string;
}

export interface Observable {
  position: number[];
  viewport_id: string;
  B_total: number[];
  B_cycle: number[];
  B_cut: number[];
  B_magnitude: number;
  E: number[];
  selectivity: number | string;
  claim_class: string;
  model_notes: string;
}

export interface ClaimRecord {
  claim_class: string;
  assumptions: string[];
  regime: string;
  frozen_version: string;
  code_digest: string;
  numerical_tolerances: Record<string, number>;
  gate_status: Record<string, boolean>;
  timestamp: string;
}
