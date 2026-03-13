# K4 Exploration Engine — Implementation Design

**Companion to:** K4_UNIFIED_ENGINE_ARCHITECTURE_v2.md (the constitution)
**Purpose:** Convert architecture into buildable software. No philosophy. No summaries. Contracts, layouts, schemas, and migration tables.

---

## 1. REPOSITORY SKELETON

```
k4-engine/
├── README.md
├── pyproject.toml                  # packaging (hatchling or setuptools)
├── Makefile                        # verify, test, lint, build-artifact
│
├── k4_frozen/                      # IMMUTABLE — copied once from v3, never edited
│   ├── __init__.py                 #   re-exports version, verify_all entry
│   ├── truth_kernel.py             #   Layer 0–1.7: M, G, D, B_face, S, SIGMA, ...
│   ├── field_engine.py             #   Layer 3–4: Biot-Savart, centroid, E-field
│   ├── symbolic_proofs.py          #   Layer 3: SymPy proofs
│   ├── bose_mesner.py              #   Layer 5
│   ├── spherical_harmonics.py      #   Layer 6
│   ├── sphere_sculpt.py            #   Layer 7
│   ├── full_wave.py                #   Layer 4W
│   ├── commutant.py                #   Layer S4
│   ├── ring_quiet.py               #   Layer 2
│   ├── inductance.py               #   Layer 4L
│   ├── null_tetrahedron.py         #   Null analysis
│   ├── policy.py                   #   Governance
│   ├── assumptions.py              #   Session preflight
│   ├── session_schema.py           #   Enums and schema types
│   ├── integration.py              #   Extension docking contracts
│   └── verify_all.py               #   182-check regression harness
│
├── k4_explorer/                    # NEW — the exploration engine
│   ├── __init__.py
│   ├── contracts.py                #   All canonical data objects (§2)
│   ├── geometry.py                 #   Geometry adapter (§6 of constitution)
│   ├── context.py                  #   FieldContext construction from frozen
│   ├── solver.py                   #   Centroid inversion, LSQ, SVD solver
│   ├── drive.py                    #   DriveSpec → edge currents → voltages
│   ├── observables.py              #   Field evaluation, selectivity, gradients
│   ├── viewports.py                #   9 canonical viewports from Doctrine
│   ├── experiment.py               #   ExperimentSpec → ExperimentResult pipeline
│   ├── trajectory.py               #   Time-domain: waveforms, SVD dimensionality
│   ├── objectives.py               #   Objective functions for field sculpting
│   ├── optimizer.py                #   Optimization loop (wraps scipy.optimize)
│   └── presets.py                  #   BASIC-BZ, NULL-CENTER, etc.
│
├── k4_artifacts/                   #   Artifact I/O — serialization, loading, export
│   ├── __init__.py
│   ├── schema.py                   #   RunArtifact, ClaimRecord JSON schema
│   ├── writer.py                   #   Write artifact bundle to disk
│   ├── reader.py                   #   Load and validate artifact bundle
│   └── digest.py                   #   Code hash / provenance computation
│
├── k4_viz/                         #   Visualization — consumes artifacts, never computes [A]/[G]
│   ├── __init__.py
│   ├── panels.py                   #   4-panel canonical layout
│   ├── figures.py                  #   Matplotlib figure generation
│   └── report.py                   #   Certification / PDF export
│
├── k4_cli/                         #   Command-line entry points
│   ├── __init__.py
│   ├── run.py                      #   `k4 run <preset|spec.json>`
│   ├── verify.py                   #   `k4 verify` — full gate check
│   └── inspect.py                  #   `k4 inspect <artifact_dir>`
│
├── tests/
│   ├── test_gates.py               #   SymPy gate re-verification
│   ├── test_contracts.py           #   Data object invariant checks
│   ├── test_vertical_slice.py      #   End-to-end BASIC-BZ run
│   ├── test_regression.py          #   18-test regression anchors
│   ├── test_imports.py             #   Import rule enforcement
│   └── test_roundtrip.py           #   w → I_edge → w decomposition roundtrip
│
├── archive/                        #   READ-ONLY — never imported at runtime
│   ├── k4_frozen_v2/               #   Previous frozen package
│   ├── k4_engine_chat.py           #   Original chat-artifact engine (~1935 lines)
│   ├── session_compiler_v3.py      #   Superseded v3 session compiler
│   └── MINING_NOTES.md             #   What was extracted and where it went
│
├── docs/
│   ├── CONSTITUTION.md             #   Architecture v2 (the constitution)
│   ├── CLAIM_TAXONOMY.md           #   [A]/[G]/[G*]/[M]/[H]/[C] definitions
│   ├── CORRECTIONS.md              #   Canonical corrections that must not regress
│   ├── ADAPTER_DOCTRINE.md         #   Geometry adapter rules
│   └── EXPERIMENT_CATALOG.md       #   Running catalog of completed experiments
│
└── runs/                           #   Artifact output directory (gitignored except examples)
    └── example_basic_bz/           #   Reference artifact for regression
```

**What remains frozen:** Everything in `k4_frozen/`. Copied verbatim from the v3 package split. The only permissible edit is bumping `__version__` if a verified correction is applied (with full diff trail).

**What is adapter code:** `k4_explorer/geometry.py`, `k4_explorer/context.py` — the bridge layer.

**What is experimental:** `k4_explorer/objectives.py`, `k4_explorer/optimizer.py` — field sculpting, not yet stabilized.

**What is archived:** Everything in `archive/`. Value-extraction only. Never imported.

---

## 2. CANONICAL DATA OBJECTS

### 2.1 ControlSpec

**Purpose:** The user's intention — what field conditions are desired.

```python
@dataclass(frozen=True)
class ControlSpec:
    """What the user wants. Immutable after construction."""
    # Primary targets (HARD constraints)
    B_target: Optional[Tuple[float,float,float]] = None     # Tesla, at centroid
    E_target: Optional[Tuple[float,float,float]] = None     # V/m, interior

    # Spatial features (HIGH priority)
    null_point: Optional[Tuple[float,float,float]] = None   # meters
    probe_points: Tuple[ProbeTarget, ...] = ()              # additional B targets

    # Soft preferences
    minimize_current: bool = True
    gradient_preference: Optional[Tuple[float,float,float]] = None

    # Limits
    I_max_per_edge: float = 10.0    # Amps
    V_max_per_vertex: float = 100.0 # Volts

    # Mode
    frequency: float = 0.0          # Hz, 0 = DC
    trajectory: Optional[TrajectorySpec] = None
```

**Invariants:** At least one of B_target, E_target, or null_point must be non-None. frequency ≥ 0. Limits > 0.

**Owner:** User / CLI / UI layer. Consumed by `k4_explorer.solver`.

**Pipeline position:** Entry point → solver.

### 2.2 GeometrySpec

**Purpose:** Describes the physical realization. Adapter input.

```python
@dataclass(frozen=True)
class GeometrySpec:
    """Physical realization description."""
    vertices: np.ndarray                    # (4,3) float64, meters
    edge_length: float                      # meters (computed from vertices)
    symmetry_class: str                     # "Td_regular" | "irregular" | "degenerate"
    wire_radius: float = 0.0               # meters, 0 = filament
    config_id: str = "D"                   # hardware configuration
    calibrated_F0: Optional[np.ndarray] = None  # (3,6) measured field matrix
    
    # Deviation report (filled by adapter)
    symmetry_deviations: Dict[str, float] = field(default_factory=dict)
    broken_assumptions: Tuple[str, ...] = ()
    claim_ceiling: str = "G"               # max claim class for this geometry
```

**Invariants:** vertices.shape == (4,3). edge_length > 0. claim_ceiling in {"A","G","G*","M","H"}.

**Owner:** `k4_explorer.geometry` (adapter produces it).

**Pipeline position:** GeometrySpec → adapter → FieldContext.

### 2.3 DriveSpec

**Purpose:** The physical drive signals — what currents/voltages to apply.

```python
@dataclass
class DriveSpec:
    """Physical drive specification. Output of solver."""
    # Hodge coordinates
    w: np.ndarray              # (3,) cycle weights, Amps
    u_coil: np.ndarray         # (3,) cut weights, Amps
    u_vertex: np.ndarray       # (3,) vertex potentials, Volts (V0=0 gauge)
    
    # Physical realization
    I_edge: np.ndarray         # (6,) edge currents, Amps
    V_drive: np.ndarray        # (6,) drive voltages, Volts (may be complex for AC)
    
    # Power budget
    P_dissipated: float        # Watts
    P_reactive: float          # VA
    I_max: float               # max |I| across edges
    V_max: float               # max |V| across edges
    
    # AC parameters (all zero for DC)
    frequency: float = 0.0
    edge_phases: Optional[np.ndarray] = None  # (6,) radians
```

**Invariants:** I_edge == M @ w + G @ u_coil (verified at construction). len(I_edge) == 6.

**Owner:** `k4_explorer.solver` produces it, `k4_explorer.drive` verifies decomposition.

**Pipeline position:** ControlSpec → solver → DriveSpec → field evaluation.

### 2.4 ObservableBundle

**Purpose:** Evaluated field quantities at one or more points.

```python
@dataclass
class ObservableBundle:
    """Field observables at a specific point or viewport."""
    position: np.ndarray            # (3,) meters
    viewport_id: Optional[str]      # "VP-01" through "VP-09", or None
    
    B_total: np.ndarray             # (3,) Tesla
    B_cycle: np.ndarray             # (3,) cycle-channel contribution
    B_cut: np.ndarray               # (3,) cut-channel contribution
    B_magnitude: float              # |B_total|
    
    E: Optional[np.ndarray]         # (3,) V/m, None if outside tetrahedron
    
    selectivity: float              # |B_cycle|/|B_cut|, inf if cut=0
    
    claim_class: str
    model_notes: str
```

**Invariants:** B_total ≈ B_cycle + B_cut (within float tolerance). selectivity ≥ 0.

**Owner:** `k4_explorer.observables` produces it.

**Pipeline position:** DriveSpec + FieldContext → observables → ObservableBundle.

### 2.5 ExperimentSpec

**Purpose:** Defines a structured parameter scan or single-point evaluation.

```python
@dataclass(frozen=True)
class ExperimentSpec:
    """What an experiment asks for. Immutable."""
    name: str
    description: str
    
    control_spec: ControlSpec               # base control (may be overridden per grid point)
    geometry_spec: GeometrySpec
    
    parameter_grid: Dict[str, np.ndarray]   # param_name → values to scan
    observables: Tuple[str, ...]            # e.g. ("B_centroid", "selectivity", "effort")
    viewports: Tuple[str, ...]              # "VP-01" through "VP-09"
    
    claim_ceiling: str                      # max claim class
    assumptions: Dict[str, Any]             # active assumptions for preflight
```

**Owner:** User defines it. `k4_explorer.experiment` consumes it.

### 2.6 ExperimentResult

**Purpose:** Complete result of running an experiment. A lab notebook entry.

```python
@dataclass
class ExperimentResult:
    """What an experiment produces. Serializable to artifact."""
    spec: ExperimentSpec
    claim_record: 'ClaimRecord'
    
    # Per-grid-point results
    results: List[Dict[str, Any]]
    
    # Quality gates
    regression_status: str              # "PASS" | "FAIL"
    sympy_gate_results: Dict[str, bool] # gate_name → passed
    
    # Certification
    tier_achieved: int                  # 1, 2, or 3
    margin: float                       # σ_min/σ_max
    constraint_residuals: List[float]
    
    # Outputs
    figures: Dict[str, str]             # name → filepath
    figure_provenance: Dict[str, 'ClaimRecord']
    
    # Timing
    wall_time_seconds: float
    timestamp: str
```

**Owner:** `k4_explorer.experiment` produces it. `k4_artifacts.writer` serializes it.

### 2.7 ClaimRecord

**Purpose:** Provenance tag. Every result carries one. This is the passport through customs.

```python
@dataclass(frozen=True)
class ClaimRecord:
    """Provenance. Immutable after construction."""
    claim_class: str                    # [A], [G], [G*], [M], [H], [C]
    assumptions: Tuple[str, ...]        # active assumption names
    regime: str                         # DC | resistive | inductive | full-wave | invalid
    
    frozen_version: str                 # "v3.0.0"
    code_digest: str                    # SHA-256 of the computation source
    
    numerical_tolerances: Dict[str, float]  # e.g. {"F0G_residual": 1e-14}
    gate_status: Dict[str, bool]        # SymPy gate outcomes at runtime
    
    timestamp: str                      # ISO 8601
```

**Invariants:** claim_class in {"A","G","G*","M","H","C"}. frozen_version matches k4_frozen.__version__. All gate_status values must be True for claim_class ∈ {"A","G"}.

**Owner:** Constructed by solver/experiment. Never mutated after creation.

### 2.8 RunArtifact

**Purpose:** The complete serializable bundle written to disk.

```python
@dataclass
class RunArtifact:
    """Everything needed to reproduce and understand a run."""
    # Identity
    run_id: str                         # UUID
    name: str
    description: str
    
    # Inputs
    control_spec: ControlSpec
    geometry_spec: GeometrySpec
    
    # Outputs
    drive: DriveSpec
    observables: List[ObservableBundle]
    experiment_result: Optional[ExperimentResult]
    
    # Provenance
    claim_record: ClaimRecord
    
    # Notes
    notes: str = ""
    ledger_entries: List[str] = field(default_factory=list)
```

**Owner:** `k4_artifacts.writer` serializes. `k4_artifacts.reader` deserializes and validates.

---

## 3. IMPORT / DEPENDENCY RULES

| Package | May Import From | Must Never Import From | Why |
|---------|----------------|----------------------|-----|
| `k4_frozen.*` | `numpy`, `scipy`, `sympy`, `typing`, other `k4_frozen.*` modules | `k4_explorer.*`, `k4_artifacts.*`, `k4_viz.*`, `k4_cli.*`, `archive.*` | Frozen core is self-contained. Exploration code must not contaminate theorems. |
| `k4_explorer.contracts` | `numpy`, `typing`, `dataclasses` | All `k4_frozen.*`, all `k4_explorer.*` logic modules | Data objects are pure schemas. No computation, no frozen imports. |
| `k4_explorer.context` | `k4_frozen.truth_kernel`, `k4_frozen.field_engine` | `k4_frozen.session_compiler`, `k4_frozen.diagnostics` | Context is a clean bridge. Session compiler is superseded. |
| `k4_explorer.geometry` | `k4_frozen.truth_kernel`, `k4_frozen.field_engine`, `k4_explorer.contracts` | `k4_explorer.solver`, `k4_explorer.optimizer` | Adapter must not depend on solver — it feeds solver. |
| `k4_explorer.solver` | `k4_explorer.context`, `k4_explorer.contracts`, `k4_frozen.truth_kernel` | `k4_frozen.field_engine` directly (use context) | Solver sees the field engine only through the FieldContext abstraction. |
| `k4_explorer.observables` | `k4_explorer.context`, `k4_explorer.contracts` | `k4_explorer.solver` | Observables evaluate fields; they don't solve for drives. |
| `k4_explorer.experiment` | `k4_explorer.*`, `k4_frozen.assumptions` | `k4_frozen.field_engine` directly | Experiment layer uses explorer APIs, not raw frozen internals. |
| `k4_explorer.optimizer` | `k4_explorer.solver`, `k4_explorer.observables`, `k4_explorer.contracts`, `scipy.optimize` | `k4_frozen.*` directly | Optimizer combines solver + observables. Never touches frozen core. |
| `k4_artifacts.*` | `k4_explorer.contracts`, `json`, `hashlib`, `pathlib` | `k4_frozen.*`, `k4_explorer` logic modules | Artifact I/O is pure serialization. No computation. |
| `k4_viz.*` | `k4_artifacts.*`, `k4_explorer.contracts`, `matplotlib` | `k4_frozen.*`, `k4_explorer.solver`, `k4_explorer.optimizer` | Viz consumes artifacts. It never computes theorem-class quantities. |
| `k4_cli.*` | `k4_explorer.*`, `k4_artifacts.*` | `k4_frozen.*` directly | CLI is a thin shell over explorer and artifacts. |
| `archive/*` | **Nothing — never imported at runtime** | Everything | Read-only reference. Value extraction goes into MINING_NOTES.md. |

**Enforcement:** `tests/test_imports.py` walks the AST of every `.py` file and asserts no forbidden imports exist. Runs in CI.

---

## 4. MINIMUM VIABLE VERTICAL SLICE

**Goal:** One runnable path from intention to saved artifact.

**Scenario:** BASIC-BZ preset. B = [0, 0, 10μT] at centroid, E = [100, 0, 0] V/m, DC, regular tetrahedron L = 0.1m.

### Modules needed (in call order)

```
k4_cli.run
  → k4_explorer.presets.BASIC_BZ          (builds ControlSpec + GeometrySpec)
  → k4_explorer.geometry.adapt_regular     (produces GeometrySpec with Td_regular)
  → k4_explorer.context.build_context      (imports from k4_frozen, builds FieldContext)
      → k4_frozen.truth_kernel (M, G, D)
      → k4_frozen.field_engine (make_vertices, field_at_centroid, e_field_volume_matrix)
      → k4_frozen.verify_all (182 gates — startup check)
  → k4_explorer.solver.solve_dc            (ControlSpec + FieldContext → DriveSpec)
  → k4_explorer.observables.evaluate_viewports (DriveSpec + FieldContext → List[ObservableBundle])
  → k4_artifacts.digest.compute_digest     (hash the solver source)
  → k4_artifacts.writer.write_artifact     (RunArtifact → disk)
```

### What can be reused safely

| Source | What | Destination | Notes |
|--------|------|-------------|-------|
| k4_frozen_v3.truth_kernel | M, G, D, all Layer 0–1 | `k4_frozen/truth_kernel.py` | Copy verbatim |
| k4_frozen_v3.field_engine | make_vertices, field_matrix, field_at_centroid, e_field_volume_matrix, centroid_inversion (DIRECT SOLVE version only) | `k4_frozen/field_engine.py` | Copy verbatim. The closed-form centroid_inversion has the wrong coefficient — use only the direct-solve `_centroid_inversion` via (F₀·M)⁻¹ |
| k4_frozen_v3.verify_all | Full 182-check harness | `k4_frozen/verify_all.py` | Copy verbatim |
| k4_frozen_v3.assumptions | SessionAssumptions, preflight | `k4_frozen/assumptions.py` | Copy verbatim |
| k4_frozen_v3.policy | Claim governance | `k4_frozen/policy.py` | Copy verbatim |

### What must be stubbed initially

| Module | Stub behavior |
|--------|---------------|
| `k4_explorer.trajectory` | Return "DC_STATIC" for frequency=0 |
| `k4_explorer.optimizer` | Not called in vertical slice |
| `k4_explorer.objectives` | Not called in vertical slice |
| `k4_viz.*` | Not called — artifact is JSON only |

### What must be rewritten

| Source | Problem | Rewrite as |
|--------|---------|-----------|
| k4_engine.py matrix copies | Embeds own M, G, D, Biot-Savart | Delete. Import from k4_frozen. |
| k4_engine.py signal layer | 27-param SignalState mixed with solve logic | Split into `drive.py` (physical realization) and `trajectory.py` (time-domain) |
| session_compiler.py | DC-only, monolithic, returns raw dict | Replace with `solver.py` returning typed DriveSpec + ClaimRecord |

### Command-line entry point

```bash
# Run a preset
k4 run basic-bz --output runs/test_001

# Run from a JSON spec file
k4 run --spec my_experiment.json --output runs/exp_042

# Verify frozen core
k4 verify

# Inspect a saved artifact
k4 inspect runs/test_001
```

Implementation: `k4_cli/run.py` is a thin argparse wrapper that calls `k4_explorer.experiment.run_single()`.

---

## 5. ARTIFACT SCHEMA

### Directory layout for a single run

```
runs/
└── 2026-03-12_basic_bz_a1b2c3d4/
    ├── manifest.json               # top-level: run_id, name, timestamp, frozen_version
    ├── spec.json                   # ControlSpec + GeometrySpec (inputs)
    ├── drive.json                  # DriveSpec (solution)
    ├── observables.json            # List[ObservableBundle] at all viewports
    ├── claim.json                  # ClaimRecord (provenance)
    ├── diagnostics.json            # SVD, tier, margin, regression results
    ├── gates.json                  # All SymPy gate outcomes
    ├── notes.md                    # Free-form session notes / ledger
    └── figures/
        ├── fig_certification.png
        ├── fig_bar_currents.png
        └── fig_provenance.json     # per-figure ClaimRecord
```

### Naming convention

```
{date}_{preset_or_name}_{run_id_short}/
```

Where `run_id_short` = first 8 chars of UUID4. Date is ISO `YYYY-MM-DD`.

### manifest.json schema

```json
{
  "run_id": "a1b2c3d4-...",
  "name": "BASIC-BZ",
  "description": "Baseline: 10µT Bz, 100 V/m Ex, DC, regular K4",
  "timestamp": "2026-03-12T14:30:00Z",
  "frozen_version": "v3.0.0",
  "code_digest": "sha256:abc123...",
  "claim_class": "G",
  "regime": "DC",
  "regression_status": "PASS",
  "gate_summary": "182/182 PASS",
  "wall_time_s": 2.4,
  "files": ["spec.json", "drive.json", "observables.json", "claim.json",
            "diagnostics.json", "gates.json", "notes.md"]
}
```

### Validation on load

`k4_artifacts.reader.load_artifact(path)` must:
1. Verify manifest.json exists and parses
2. Verify frozen_version matches current k4_frozen.__version__
3. Verify code_digest matches current solver source (warn if mismatch, don't fail)
4. Deserialize all JSON into typed data objects
5. Re-check ClaimRecord invariants (claim_class valid, gates consistent)

---

## 6. MIGRATION PLAN

| Module | Role | Claim Ceiling | Action | Destination | Comments |
|--------|------|---------------|--------|-------------|----------|
| truth_kernel.py (v3) | Integer matrices, Layer 0–1.7 | [A] | **Copy verbatim** | `k4_frozen/truth_kernel.py` | Immutable |
| field_engine.py (v3) | Biot-Savart, centroid | [G] | **Copy verbatim** | `k4_frozen/field_engine.py` | Immutable. Use direct-solve inversion only |
| symbolic_proofs.py (v3) | SymPy proofs | [G] | **Copy verbatim** | `k4_frozen/symbolic_proofs.py` | Immutable |
| bose_mesner.py (v3) | Algebra module | [A]+[G] | **Copy verbatim** | `k4_frozen/bose_mesner.py` | Immutable |
| spherical_harmonics.py (v3) | l=1 synthesis | [G] | **Copy verbatim** | `k4_frozen/spherical_harmonics.py` | Immutable |
| sphere_sculpt.py (v3) | Sculpting | [G] | **Copy verbatim** | `k4_frozen/sphere_sculpt.py` | Immutable |
| full_wave.py (v3) | Z(ω), retarded | [G*] | **Copy verbatim** | `k4_frozen/full_wave.py` | Immutable. Regime limits documented |
| commutant.py (v3) | S₄ rep theory | [A]+[G] | **Copy verbatim** | `k4_frozen/commutant.py` | Immutable |
| ring_quiet.py (v3) | Ring-edge cancellation | [A] | **Copy verbatim** | `k4_frozen/ring_quiet.py` | Immutable |
| inductance.py (v3) | Neumann integrals, command_dc/ac | [M] | **Copy verbatim** | `k4_frozen/inductance.py` | Immutable. command_dc/ac provide reference implementations |
| null_tetrahedron.py (v3) | Null analysis | [G]+[M] | **Copy verbatim** | `k4_frozen/null_tetrahedron.py` | Immutable |
| diagnostics.py (v3) | Figure generation | N/A | **Copy verbatim** | `k4_frozen/diagnostics.py` | For USPTO figure regression only |
| session_schema.py (v3) | Enums, types | [A] | **Copy verbatim** | `k4_frozen/session_schema.py` | ConfigID, BModelTier, etc. |
| session_compiler.py (v3) | DC session solver | [M] | **Archive** | `archive/session_compiler_v3.py` | Superseded by k4_explorer.solver |
| policy.py (v3) | Claim governance | [A] | **Copy verbatim** | `k4_frozen/policy.py` | Immutable |
| assumptions.py (v3) | Session preflight | [A] | **Copy verbatim** | `k4_frozen/assumptions.py` | Immutable |
| integration.py (v3) | Extension docking | [A] | **Copy verbatim** | `k4_frozen/integration.py` | Immutable |
| verify_all.py (v3) | 182-check harness | — | **Copy verbatim** | `k4_frozen/verify_all.py` | Startup gate |
| **k4_engine.py** (chat) | Exploration engine | [A] gates + [M] | **Mine + rewrite** | Split across `k4_explorer/*` | Remove all embedded matrices. Port signal layer to `drive.py`, modes to solver, viewports to `viewports.py`, SVD to `trajectory.py`. |
| k4_frozen_v2 (full) | Previous package | [A]–[M] | **Archive** | `archive/k4_frozen_v2/` | Never import at runtime |
| K4_CONTROL_DOCTRINE.md | Operational spec | — | **Copy to docs** | `docs/CONSTITUTION.md` (appended or linked) | Reference document |
| K4_CANONICAL_PANELS.md | UI spec | — | **Copy to docs** | `docs/PANELS_SPEC.md` | Reference for k4_viz |
| K4_V3_EXTENSIONS_APPENDIX.md | Vision | [H]/[C] | **Copy to docs** | `docs/EXTENSIONS.md` | Reference only, never imported |

---

## 7. FIRST IMPLEMENTATION ROADMAP

### Phase 1: Repo Skeleton + Contracts (2 days)

**Objective:** Establish the package structure, freeze the frozen core, stabilize data objects.

**Outputs:**
- Complete repo skeleton with all directories
- `k4_frozen/` populated from v3 split
- `k4_explorer/contracts.py` with all 8 data objects
- `tests/test_imports.py` enforcing dependency rules
- `tests/test_gates.py` running verify_all

**Risks:** v3 split may have subtle file-boundary issues (cross-imports between modules). Mitigate by running verify_all immediately after split.

**Gate:** `k4 verify` passes 182/182. `tests/test_imports.py` passes.

### Phase 2: Minimum Vertical Slice (3 days)

**Objective:** BASIC-BZ runs end-to-end and produces a saved artifact.

**Outputs:**
- `k4_explorer/geometry.py` — `adapt_regular(L)` → GeometrySpec
- `k4_explorer/context.py` — `build_context(GeometrySpec)` → FieldContext
- `k4_explorer/solver.py` — `solve_dc(ControlSpec, FieldContext)` → DriveSpec
- `k4_explorer/observables.py` — `evaluate_viewports(DriveSpec, FieldContext)` → List[ObservableBundle]
- `k4_explorer/presets.py` — BASIC_BZ preset
- `k4_artifacts/writer.py` — writes artifact bundle
- `k4_cli/run.py` — `k4 run basic-bz`

**Risks:** Centroid inversion must use the direct-solve path, not the closed-form with wrong coefficient. Regression values must match v3 compiler output.

**Gate:** `k4 run basic-bz` produces artifact. B_error_relative < 10⁻¹². Saved artifact loads cleanly via `k4 inspect`. Regression anchors match.

### Phase 3: Artifact System + Regression (2 days)

**Objective:** Artifacts are reproducible, loadable, and regression-tested.

**Outputs:**
- `k4_artifacts/reader.py` — load + validate
- `k4_artifacts/digest.py` — SHA-256 of solver source
- `tests/test_vertical_slice.py` — end-to-end BASIC-BZ regression
- `tests/test_roundtrip.py` — w → I_edge → decompose → w matches
- 7 canonical presets all produce valid artifacts
- `runs/example_basic_bz/` committed as reference artifact

**Risks:** JSON serialization of numpy arrays (use `.tolist()`). Floating-point non-determinism across platforms (use relative tolerances).

**Gate:** All 7 presets produce valid artifacts. Decomposition roundtrip error < 10⁻¹⁴. Reference artifact bit-reproducible on same platform.

### Phase 4: Objective Functions for Field Sculpting (3 days)

**Objective:** Define and implement the first optimization targets.

**Outputs:**
- `k4_explorer/objectives.py` with objective functions:
  - `null_placement_cost(r_null, context)` — effort to place B=0 at r_null
  - `gradient_shaping_residual(target_grad, context)` — ∇B mismatch
  - `dipole_purity(w, context)` — fraction of far-field power in l=1
  - `probe_match(B_targets_at_points, context)` — multi-point B matching
- Each objective returns a scalar loss + gradient (if available) + ClaimRecord

**Risks:** Gradient computation for off-centroid objectives requires careful numerical differentiation (field matrix is not smooth near edges). Use finite differences with wire-radius floor.

**Gate:** Each objective evaluates without error on 100 random inputs. Gradient (finite-diff) matches analytical gradient where available.

### Phase 5: Optimization / Inverse Design (3 days)

**Objective:** Wrap objectives into an optimization loop that finds optimal drive parameters.

**Outputs:**
- `k4_explorer/optimizer.py` — wraps `scipy.optimize.minimize` (and optionally `least_squares`)
- Supports: constrained optimization (current limits), multi-objective (weighted sum), trajectory optimization (sequence of DriveSpecs)
- Each optimization run produces an ExperimentResult with full provenance

**Risks:** Non-convexity for off-centroid multi-point targets. Mitigate with multi-start. Centroid-only objectives are convex (linear system) — start there.

**Gate:** Null placement at 10 interior points converges in < 100 iterations each. Optimized effort within 5% of analytical minimum (where known).

### Phase 6: Visualization + Shareable Demos (2 days)

**Objective:** Generate publication-quality figures and shareable reports from artifacts.

**Outputs:**
- `k4_viz/figures.py` — bar charts (edge currents in mA), selectivity profiles, viewport tables
- `k4_viz/panels.py` — 4-panel canonical layout (static matplotlib version)
- `k4_viz/report.py` — markdown/PDF certification report
- Demo notebook: `docs/demo_basic_bz.ipynb`

**Risks:** Visualization layer accidentally computing field values instead of reading from artifacts. Mitigate with import rule enforcement.

**Gate:** Figures match v3 diagnostics output for BASIC-BZ. Report includes all ClaimRecord fields. No `k4_frozen` imports in `k4_viz/`.

---

## 8. FIRST FIELD-SCULPTING OBJECTIVES

### 8.1 Null Placement (Priority 1)

**What is sculpted:** Position of B = 0 inside the tetrahedron.

**Observable:** |B(r_null)| minimized, |B(centroid)| maintained at target.

**Control DOF:** 6 edge currents (w + u_coil). Centroid B consumes 3 DOF (w). Null consumes up to 3 DOF (mixed w + u_coil). Budget: 6 DOF, 6 constraints = exactly determined.

**Objective:** minimize |B(r_null)|² subject to B(centroid) = B_target.

**Constraints:** |I_edge| ≤ I_max per edge.

**Failure modes:** Null too close to an edge (field matrix singular). Null on conditioning ridge at ~0.5L on vertex axes (κ peaks). Null outside tetrahedron (no E model, Earnshaw forces saddle).

**Known performance:** All tested interior nulls are true nulls (positive-definite Hessian). Effort varies 2:1 around orbit at 0.1L. Centroid null costs zero (u_coil = 0 trivially).

### 8.2 Gradient Shaping (Priority 2)

**What is sculpted:** ∇B direction/magnitude at centroid or nearby point.

**Observable:** 5 independent gradient components (3×3 symmetric traceless tensor from Maxwell).

**Control DOF:** w controls both B and ∇B at centroid — choosing B determines ∇B (no free gradient DOF from cycle alone). Cut-coil u_coil contributes ~14% gradient at centroid, more off-centroid. True gradient freedom requires evaluation at a point where cut contributes.

**Objective:** minimize ‖∇B_achieved − ∇B_target‖² subject to B(centroid) = B_target.

**Constraints:** Current limits. Off-centroid evaluation point must stay within model validity (> wire_radius from edges).

**Failure modes:** At centroid, gradient is fully determined by w — no optimization possible (it's a linear consequence of the B choice). Must go off-centroid for gradient shaping freedom.

### 8.3 Dipole Steering with Leakage Suppression (Priority 3)

**What is sculpted:** External dipole direction via cut-coil channel, with minimal quadrupole leakage.

**Observable:** Far-field dipole moment direction + magnitude. Quadrupole/octupole power ratio.

**Control DOF:** u_coil (3 DOF) for dipole steering. w (3 DOF) can be used to suppress higher multipoles or maintain centroid B.

**Objective:** maximize dipole alignment with target direction, minimize ‖quadrupole‖/‖dipole‖.

**Constraints:** Total current budget. Centroid B maintained (if desired — costs 3 w DOF).

**Failure modes:** Dipole direction and centroid B compete for resources if both active. Pure cut-coil gives full dipole rank-3 control without centroid disturbance (by F₀·G = 0).

### 8.4 Internal vs External Shaping Tradeoff (Priority 4)

**What is sculpted:** Simultaneous interior field pattern + exterior radiation pattern.

**Observable:** B at centroid (interior), dipole moment (exterior), selectivity at 1L and 3L.

**Control DOF:** Full 9 DOF (w, u_coil, u). Interior B uses w. Exterior dipole uses u_coil. E uses u. By Hodge orthogonality, these are formally independent at centroid.

**Objective:** Pareto frontier: sweep trade between |B_centroid − target| and |dipole − target_dipole|.

**Constraints:** Current limits, voltage limits.

**Failure modes:** Off-centroid, cycle and cut channels interact. The independence is exact only at the centroid. Moving the evaluation point off-center introduces cross-coupling that grows with distance.

### 8.5 Local Probe Matching (Priority 5)

**What is sculpted:** B-field values at 2+ specified interior points simultaneously.

**Observable:** B(r₁), B(r₂), ..., B(rₖ) at k points.

**Control DOF:** 6 (edge currents). Each point imposes 3 constraints. k=1: exactly determined. k=2: 6 constraints from 6 DOF, rank depends on point placement. k>2: overconstrained — least-squares with graceful degradation.

**Objective:** minimize Σᵢ ‖B(rᵢ) − Bᵢ_target‖², optionally weighted by priority.

**Constraints:** Current limits. Points must be > wire_radius from edges.

**Failure modes:** Two points on the same C₃ axis may have nearly parallel F(r) rows → singular system. Known: 2-point on symmetry axes gives rank 5 (not 6). Off-axis points give rank 6 with κ up to ~272.

---

## 9. CONTRADICTION / RISK LEDGER

| # | Trap | Mechanism | Prevention |
|---|------|-----------|------------|
| 1 | **Duplicated frozen logic** | k4_engine.py or new code re-derives M, G, F₀ instead of importing | Import rules (§3) + test_imports.py. If it's in k4_frozen, it's imported, never re-implemented. |
| 2 | **Category collapse: exact ↔ numerical** | A result at 10⁻¹⁴ is treated as proven. Or a proven result is silently downgraded by wrapping it in float arithmetic | ClaimRecord is mandatory. Gates check Integer(0) type, not magnitude. Every float-valued result is [M] unless proven otherwise. |
| 3 | **Overexposing raw coil parameters** | User/optimizer directly sets 6 edge currents without going through Hodge decomposition, bypassing the cycle/cut control structure | DriveSpec always contains both (w, u_coil) AND I_edge. Solver constructs I_edge from Hodge coordinates. Direct I_edge injection must carry [M] ceiling and log a warning. |
| 4 | **UI becomes authoritative** | A visualization panel computes a field value and displays it, and that value is treated as the result (instead of the artifact) | Viz imports only from k4_artifacts. Viz never calls field_engine. All displayed values come from stored ObservableBundles. |
| 5 | **Geometry extension treated as theorem-preserving** | An irregular tetrahedron adapter claims [G] for F₀·G = 0 | GeometrySpec.claim_ceiling is set by the adapter and cannot exceed the symmetry class ceiling. "irregular" → [M] max. |
| 6 | **Centroid inversion formula regression** | Someone re-introduces the wrong closed-form w₁ = −√6·L·(Bx+By)/32 | Regression test: solve_dc([0,0,10e-6]) must produce I_edge matching the direct-solve reference value to 10⁻¹². The closed-form function in field_engine is kept but deprecated. |
| 7 | **v2/v3 contamination** | A module accidentally imports from archive/k4_frozen_v2 | test_imports.py scans all imports. v2 directory has no `__init__.py` (not a package). |
| 8 | **Silent assumption change** | Switching from DC to AC without updating SessionAssumptions | preflight() is mandatory before any solve. It checks frequency vs model validity. |
| 9 | **Breathing direction universalized** | Code assumes [1,1,1] is the transverse plane normal for all configs | Each config's breathing vector is stored in a canonical table (from Mar 7 session). trajectory.py references it per-config. |
| 10 | **Artifact figures without provenance** | A figure is generated and shared without its ClaimRecord, losing the exact conditions under which it was computed | figure_provenance dict in ExperimentResult. Every figure file has a companion `_provenance.json`. |

---

## 10. DO-NOT-DO LIST

1. **Do not embed M, G, D, or F₀ in any file outside k4_frozen/.** Import them.

2. **Do not call `field_engine.centroid_inversion()` (the closed-form).** It has the wrong coefficient. Use `solver.solve_dc()` which calls the direct-solve `(F₀·M)⁻¹ · B_target`.

3. **Do not import anything from `archive/` at runtime.** It is not a package. It has no `__init__.py`.

4. **Do not let the optimizer output a DriveSpec without re-evaluating observables.** The optimizer finds parameters; the field engine verifies them. Trust the verification, not the optimizer.

5. **Do not display a field value that was not read from a stored ObservableBundle.** Visualization computes layout, not physics.

6. **Do not promote a numerical result to [G] or [A] without a named proof.** Write "[M] → [G] via ___" and fill in the blank, or it stays [M].

7. **Do not assume F₀·G = 0 for irregular geometries.** It requires T_d symmetry. The adapter must check and set claim_ceiling accordingly.

8. **Do not use the standard 3-phase pattern [cos, cos−120°, cos+120°] as universal AC drive.** It privileges Config 0's breathing direction. Each config has its own transverse plane.

9. **Do not run an experiment without calling `preflight()`.** It catches regime violations, tier violations, and conductor model leaks.

10. **Do not treat the 7 canonical presets as "just demos."** They are regression anchors. If a preset's output changes, the engine has drifted. Investigate before proceeding.

11. **Do not generate figures at DPI < 300 for any output intended to survive.** USPTO requires it. The habit should be universal.

12. **Do not use `numpy.float64` results as proof of exactness.** If you need [A], use SymPy. If you used numpy, it's [M] at best.
