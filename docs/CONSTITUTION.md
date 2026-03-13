# K4 Unified Exploration Engine — Architecture & Build Plan (v2)

**Session:** 2026-03-12
**Constitution:** UNIFIED_ENGINE_BOOTSTRAP.md
**Sources:** k4_frozen_v2 (153/153), k4_frozen_v3 (182/182), K4_CONTROL_DOCTRINE, K4_CANONICAL_PANELS, K4_V3_EXTENSIONS_APPENDIX, plus deep mine of 12+ chat sessions (Jan–Mar 2026)
**Revision:** v2 — incorporates structured review recommendations (claim taxonomy, non-negotiables, import rules, adapter doctrine, provenance contracts)

---

## 0. Executive Synthesis

The K4 project has accumulated substantial proven mathematics, a verified numerical engine, a mature control doctrine, and a rich body of exploration results — but these are scattered across frozen packages, chat artifacts, and design documents with no unified runtime. This document assembles the minimum viable exploration engine from those pieces.

**What exists and is solid:**

- A truth kernel with 40+ identities proven to Integer(0) via SymPy (Layers 0–1.7), unconditional
- A field engine with Biot-Savart + barycentric E-field + centroid inversion, verified across 18 regression tests (Layer 3–4)
- Extended algebraic modules: Bose-Mesner, spherical harmonics, sphere sculpting, full-wave, commutant/S₄ rep theory, ring-quiet (v3 Layers 5–8)
- A 9D control doctrine with observable catalog, 9 canonical viewports, 4-panel workspace spec
- A simulation engine (k4_engine.py, ~1935 lines) with 27-parameter signal layer, 12 operating modes, SVD trajectory analysis
- Deep exploration results on AC orbits, selectivity crossover, null placement, multipole selection rules, and the S₄ commutant structure

**What is missing:**

- A single importable package that composes these assets into a runnable exploration engine
- Clean adapter contracts between the frozen algebraic core and the numerical/exploration layers
- A structured experiment runner with reproducible artifact generation
- Integration of the scattered corrections (centroid inversion formula, vertex stars vs face triangles, AC orbit planes, etc.) into a single canonical codebase

**Risk summary:** The dominant immediate risks are architectural rather than foundational, given the strength of the frozen proofs. Module overlap between v2/v3/k4_engine.py, untested regime boundaries (especially AC/full-wave), and the gap between the rich design documents (Doctrine, Panels) and actual runnable code are the primary concerns.

---

## 0.1 Non-Negotiables

These rules are absolute for every action in this session and every module in the engine.

1. **Never duplicate frozen matrices in exploration code.** All algebra comes from k4_frozen_v3 via import. No embedded copies of M, G, D, F₀, or any derived matrix.

2. **Never upgrade a numerical observation to theorem status without an explicit proof path.** A result verified to 10⁻¹⁴ is [M] until a symbolic/algebraic proof promotes it. The notation "[M] → [G] via ___" must name the missing step.

3. **Never mix v2 and v3 imports in the same runtime path.** v3 is canonical. v2 is archive-only, never imported at runtime.

4. **Every experiment must emit claim class, assumptions, and regime.** No naked numbers. Every output carries its ClaimRecord.

5. **Every geometry extension must pass through an adapter into frozen control coordinates.** Physical windings, irregular tetrahedra, multi-cell arrays — all map into (w, u_coil, u) via a GeometryAdapterResult. The frozen truth kernel is never modified to accommodate hardware.

6. **Never blur the four session-doctrine classes** (Proven / Derived-but-Unverified / Engineering Heuristic / Speculative). If uncertain which class applies, choose the weaker one.

---

## 0.2 Claim Taxonomy

Every result, output, and displayed quantity in this engine carries one of these tags. This is the formal legend — use no other classification.

| Tag | Name | Definition | Promotion requires |
|-----|------|------------|-------------------|
| **[A]** | Algebraic exact | Unconditional. Integer(0) via SymPy, or pure graph/representation theory. No geometry, no physics, no model. | N/A — this is the ceiling |
| **[G]** | Geometric exact | Exact under named premises (regular K₄ + specific physics law). Premises must be stated. | Proof that premises are unnecessary |
| **[G*]** | Model-limited analytic | Valid only within a stated regime (e.g., full-wave without capacitance). Regime boundaries must be documented. | Remove the regime limitation |
| **[M]** | Model-dependent numerical | Verified computationally across test suites or regression. Not a proof. | Construct algebraic/symbolic proof |
| **[H]** | Hardware / engineering heuristic | Useful design guidance, approximation strategy, or practical control intuition. Not a theorem. | Experimental validation + analytical model |
| **[C]** | Conjectural | Incomplete proof path, or speculative. Must state what's missing. | Complete the proof |

**Promotion rules:** A result may only be promoted to a stronger class by explicit action with a named proof or validation. Promotion never happens silently. Demotion (discovering a hidden premise) is always allowed and should be announced immediately.

---

## 1. Frozen Core Map

### 1A. Immutable — Never Touch

These are unconditional algebraic facts [A]. They hold for ANY K₄ regardless of geometry, physics, or model.

| ID | Statement | Proof Method |
|----|-----------|-------------|
| T1.1 | M^T · G = 0₃ₓ₃ (cycle ⊥ cut) | Integer(0) SymPy |
| T1.2 | D · M = 0₄ₓ₃ (cycles satisfy KCL) | Integer(0) SymPy |
| T1.3 | M^T M = G^T G = 4I₃ − J₃ (Gram) | Integer SymPy |
| T1.4 | det(M^T M) = 16 | Integer SymPy |
| T1.5 | det([M|G]) = ±16 (full rank decomposition) | Integer SymPy |
| T1.6 | M⁺·G = G⁺·M = 0₃ₓ₃ | Rational SymPy |
| T1.7 | P_cycle + P_cut = I₆ | Rational SymPy |
| T1.8 | P_cycle · P_cut = 0₆ₓ₆ | Rational SymPy |
| P4 | rank(D·G) = 3 (every nonzero cut violates KCL) | Integer SymPy |
| P5 | D_red^T = G (identity, not just same span) | Integer(0) SymPy |
| P12 | Min-norm vertex injection is pure cut | Integer(0) SymPy |
| Chain | D · B_face = 0, B^T · D^T = 0 (∂²=0) | Integer(0) SymPy |
| L₁ | D^T D + B B^T = 4·I₆ (edge Laplacian scalar) | Integer SymPy |
| Unique | K₄ is the only Kₙ with dim(cycle)=dim(cut)=3 | Algebraic |
| ED.1 | Δ · M = 0 (edge directions annihilate cycles) | Integer(0) SymPy |
| T3.1 core | C_INT · G = 0 (STRUCTURAL core of cut annihilation) | Integer(0) SymPy |
| T3.2 core | det(C_INT · M) = 32 | Integer SymPy |
| T3.3 core | (CM)^T(CM) eigenvalues = {4, 16} | Integer SymPy |
| Σ eigenvalues | Σ·M = −2·M, Σ·G = +2·G (genuine eigenspaces in ℝ⁶) | Integer SymPy |
| M^T·Σ·G = 0 | Hodge-inductance cross-term vanishes | Integer(0) SymPy |
| Ring-quiet | w₁+w₂+w₃=0 silences one face's edges (face-specific) | Integer(0) SymPy |
| Commutant | G_grad ∈ span{I₆, Σ} for any equivariant kernel; A_opp selection rule | [A]+[G] |
| 7-line 2-design | 7 T_d axes form projective 2-design, frame bound 7/3 | [A] Schur on Sym²(T₂) |
| All irreps mult-1 | T₂⊗T₂ = A₁⊕E⊕T₁⊕T₂ (each multiplicity 1) | [A] S₄ characters |
| Gradient irrep complementarity | M^T·G_grad·G = 0 for any kernel | [A] Integer(0) |

### 1B. Geometry-Dependent Exact — Requires Regular K₄ + Named Model

| ID | Statement | Claim | Key Premise |
|----|-----------|-------|---------|
| T3.1 | F₀·G = 0 (cut annihilation at centroid) | [A]+[G] | T_d symmetry only — survives any T_d-preserving field model including retarded |
| T3.2 | det(F₀·M) ≠ 0, rank(F₀·M) = 3 | [G] | Regular K₄ + any non-degenerate field model |
| T3.3/P13 | κ(Gram of F₀·M) = 2 | [G] | Regular K₄ + Biot-Savart. Gram condition number; κ_intrinsic=1 at centroid |
| Centroid inversion | w = (F₀·M)⁻¹ · B_target | [G] | Direct solve. w₁ = −(Bx+By)/(2k), k = 2μ₀√6/(3πL) |
| ζ₄ = 1/7 | Gradient ratio ‖dF·G‖/‖dF·M‖ | [G] | 9K₁ = 7J₀ (Biot-Savart integral identity) |
| ζ₄² formula | (α+2β)/(α−2β) = λ_cut/λ_cycle | [A]+[G] | Commutant eigenvalue ratio |
| E_vol rank 3, κ=2 | E uniform interior, 3 basis directions at 109.5° | [G] | Barycentric model |
| M^T·Z(ω)·G = 0 | Impedance block-diagonal in Hodge basis | [G*] | Commutant + l₁⊥l₂ |

### 1C. Canonical Corrections (must not regress)

| Correction | Wrong | Right | Source |
|------------|-------|-------|--------|
| Centroid inversion | w₁ = −√6·L·(Bx+By)/32 (missing μ₀) | w₁ = −(Bx+By)/(2k), k = 2μ₀√6/(3πL) | Fixed Mar 7 |
| Vertex stars vs face triangles | "4 face triangles fail at centroid" | 4 VERTEX STARS fail (common vertex). Face triangles span R³ with κ=2 | k4_engine v3 |
| E-field mutual angle | 70.5° | 109.5° (arccos(−1/3)) | k4_engine v3 |
| Gram condition number | κ=2 unqualified | "Gram condition number κ=2"; κ_intrinsic=1 | Doctrine |
| AC orbit dimensionality | "All AC at centroid = 2D" | Each config has OWN transverse plane; two configs → genuine 3D orbits | Mar 7 session |
| AM 3-phase | AM gives rotation | AM 3-phase = null. Direction must change | Doctrine |
| Ring-quiet scope | Universal condition | Face-specific only | Doctrine |
| "Monopole" language | Casual use | Always "monopole-like" (r⁻² scaling only) | Feb 26 session |
| F₀·G=0 premise | Requires magnetostatic | Requires T_d symmetry only | Feb 26 session |
| Vertex oscillator framing | "Return paths" | Purged. Vertex hardware = cut-associated DOF | PPA v6.1+ |

---

## 2. Module Inventory

| Module | Layer | Lines | Tests | Claim Ceiling | Recommendation |
|--------|-------|-------|-------|---------------|----------------|
| truth_kernel.py (v3) | 0–1.7 | ~460 | 30+ | [A] | **FREEZE as canonical** |
| field_engine.py (v3) | 3–4 | ~350 | verify_layer4 | [G] centroid | **FREEZE** |
| symbolic_proofs.py (v3) | 3 | ~300 | Integer(0) | [G] | FREEZE |
| bose_mesner.py (v3) | 5 | ~200 | verified | [A]+[G] | FREEZE |
| spherical_harmonics.py | 6 | ~200 | verified | [G] | FREEZE |
| sphere_sculpt.py (v3) | 7 | ~150 | verified | [G] | FREEZE |
| full_wave.py (v3) | 4W | ~250 | verified | [G*] | FREEZE (regime-limited) |
| commutant.py (v3) | 8 | ~350 | verified | [A]+[G] | FREEZE |
| ring_quiet.py (v3) | 2 | ~100 | verified | [A] | FREEZE |
| inductance.py (v3) | 4L | ~500 | verified | [M] | FREEZE |
| null_tetrahedron.py | 4 | ~250 | analysis | [G]+[M] | FREEZE |
| diagnostics.py (v3) | viz | ~400 | 8 figs | N/A | KEEP for USPTO figures |
| session_schema.py (v3) | policy | ~400 | types | [A] | **ADAPT** — extract interfaces |
| session_compiler.py (v3) | run | ~400 | 12 reg | [M] | **ARCHIVE** — superseded by k4_engine |
| policy.py (v3) | gov | ~300 | enforce | [A] | KEEP |
| assumptions.py (v3) | gov | ~640 | preflight | [A] | KEEP |
| integration.py (v3) | ext | ~380 | types | [A] | KEEP |
| verify_all.py (v3) | test | ~250 | 182 | — | KEEP as regression gate |
| **k4_engine.py** | exploration | ~1935 | 14+18 | [A] gates + [M] | **ADAPT** — remove duplicated algebra/field definitions, replace with imported canonical sources from v3 |
| k4_frozen_v2 (full) | all | ~6000 | 153 | [A]–[M] | **ARCHIVE** — superseded, never imported at runtime |

---

## 3. Import Rules

These rules prevent circular dependency and category contamination.

| Package | May Import From | Must Never Import From |
|---------|----------------|----------------------|
| `k4_frozen_v3.truth_kernel` | `numpy`, `typing` only | Any other k4 module |
| `k4_frozen_v3.field_engine` | `truth_kernel`, `numpy`, `scipy` | `k4_explorer.*`, `k4_frozen_v2.*` |
| `k4_frozen_v3.*` (any module) | Other `k4_frozen_v3` modules, standard libs | `k4_explorer.*`, `k4_frozen_v2.*` |
| `k4_explorer.context` | `k4_frozen_v3.truth_kernel`, `k4_frozen_v3.field_engine` | Nothing else from v3 internals |
| `k4_explorer.signal` | `k4_frozen_v3.truth_kernel` (for M, G only) | `k4_frozen_v3.field_engine` |
| `k4_explorer.solver` | `k4_explorer.context`, `k4_frozen_v3.truth_kernel` | Direct field computation (goes through context) |
| `k4_explorer.experiment` | `k4_explorer.*`, `k4_frozen_v3.assumptions` | Direct `k4_frozen_v3.field_engine` calls |
| `k4_explorer.visualization.*` | `k4_explorer.experiment` (consumes artifacts) | Must not compute theorem-class [A]/[G] quantities |
| Archive modules (`k4_frozen_v2`, old scripts) | **Never imported at runtime** | Everything — read-only reference for value extraction |

**Enforcement:** A CI check or import-time assertion that no `k4_explorer` symbol appears in any `k4_frozen_v3` module's namespace.

---

## 4. Architecture Proposal

```
┌──────────────────────────────────────────────────────────┐
│              UNIFIED EXPLORATION ENGINE                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  LAYER A: TRUTH KERNEL (immutable, [A])                  │
│    k4_frozen_v3: truth_kernel, symbolic_proofs,           │
│    ring_quiet, commutant                                  │
│                                                          │
│  LAYER B: FIELD ENGINE (model-dependent, [G]/[M])        │
│    k4_frozen_v3: field_engine, inductance, full_wave,     │
│    bose_mesner, spherical_harmonics, sphere_sculpt,       │
│    null_tetrahedron                                       │
│                                                          │
│  LAYER C: EXPLORATION ENGINE (new: k4_explorer/)         │
│    context.py    — FieldContext from v3 modules           │
│    signal.py     — 27-param SignalState                   │
│    modes.py      — 12 operating modes                     │
│    solver.py     — SVD + centroid inversion               │
│    trajectory.py — time-domain + dimensionality           │
│    viewports.py  — 9 canonical viewports                  │
│    observables.py— B, E, selectivity, gradients           │
│    experiment.py — scan runner + artifact generation       │
│                                                          │
│  LAYER D: VISUALIZATION / IO                             │
│    panels.py, figures.py, artifacts.py, report.py         │
│                                                          │
│  LAYER E: GOVERNANCE                                     │
│    k4_frozen_v3: policy, assumptions, integration,        │
│    verify_all (182-check startup gate)                    │
│                                                          │
│  ARCHIVE: k4_frozen_v2, extensions appendix, earlier code │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Contract Boundaries

### 5A. Canonical Cross-Layer Objects

These are the only conceptual passports that data carries between layers. Every cross-layer transfer must be expressible as one of these.

```python
@dataclass
class FrozenBasis:
    """Immutable reference to the algebraic core. Constructed once, never mutated."""
    M: np.ndarray          # (6,3) int64 — cycle basis
    G: np.ndarray          # (6,3) int64 — cut basis  
    D: np.ndarray          # (4,6) int64 — incidence
    B_face: np.ndarray     # (6,4) int64 — face boundary
    SIGMA: np.ndarray      # (6,6) int64 — signed adjacency
    version: str           # "v3.0.0"
    gate_status: Dict[str, bool]  # all SymPy gates at construction

@dataclass
class GeometryAdapterResult:
    """Output of mapping any physical realization into frozen coordinates."""
    V: np.ndarray          # (4,3) vertex coordinates
    L: float               # edge length (m)
    F0: np.ndarray         # (3,6) field matrix at centroid
    F0M: np.ndarray        # (3,3) = F0 @ M
    F0M_inv: np.ndarray    # (3,3) inverse
    E_vol: np.ndarray      # (3,3) E-field volume matrix
    field_matrix_func: Callable     # r → F(r)
    symmetry_class: str    # "Td_regular", "irregular", "degenerate"
    symmetry_deviations: Dict       # what's broken, preserved, approximate
    broken_assumptions: List[str]   # which frozen assumptions don't hold
    claim_ceiling: str     # max claim class for this geometry
    
@dataclass
class DriveSpec:
    """The 27-parameter instantaneous state."""
    w: np.ndarray              # (3,) cycle weights
    u_coil: np.ndarray         # (3,) cut weights
    u: np.ndarray              # (3,) vertex potentials
    edge_frequencies: np.ndarray    # (6,) Hz — zero for DC
    edge_phases: np.ndarray         # (6,) radians
    vertex_osc_params: np.ndarray   # (3,3) amplitude, freq, phase per vertex

@dataclass
class ObservableBundle:
    """Evaluated observables at a specific point or viewport."""
    position: np.ndarray        # (3,) evaluation point
    viewport_id: Optional[str]  # "VP-01" through "VP-09"
    B_total: np.ndarray         # (3,) Tesla
    B_cycle: np.ndarray         # (3,) cycle contribution
    B_cut: np.ndarray           # (3,) cut contribution
    E: np.ndarray               # (3,) V/m
    selectivity: float          # |B_cycle|/|B_cut|
    claim_class: str
    model_notes: str

@dataclass
class ClaimRecord:
    """Provenance tag attached to every result."""
    claim_class: str            # [A], [G], [G*], [M], [H], [C]
    assumptions: List[str]      # active assumptions
    regime: str                 # DC, resistive, inductive, full-wave, invalid
    frozen_version: str         # "v3.0.0"
    gate_status: Dict[str, bool]
    code_digest: str            # hash of the computation code
    numerical_tolerances: Dict[str, float]
    timestamp: str

@dataclass
class ExperimentSpec:
    """What an experiment asks for."""
    name: str
    description: str
    parameter_grid: Dict[str, np.ndarray]
    observables: List[str]
    viewports: List[str]
    claim_ceiling: str
    assumptions: 'SessionAssumptions'

@dataclass
class ExperimentResult:
    """What an experiment produces. This is a lab notebook entry, not a display object."""
    spec: ExperimentSpec
    claim_record: ClaimRecord
    results: List[Dict]
    regression_gate_status: str     # PASS/FAIL
    gate_results: Dict[str, bool]
    figures: Dict[str, str]         # name → filepath
    figure_provenance: Dict[str, ClaimRecord]  # per-figure claim
    certification: Dict
```

### 5B. Exactness Preservation Rules

| Crossing | Rule |
|----------|------|
| Layer A data used in Layer B | Must pass SymPy gate before any float conversion |
| Layer B result claimed as [G] | Must verify F₀·G residual < 10⁻¹² at runtime |
| Layer C scan claimed [M] | Must declare assumptions via preflight() |
| Any displayed result | Must carry claim class badge (PROVEN/ANALYTIC/NUMERICAL) |
| Any stored artifact | Must include full ClaimRecord with code_digest, frozen_version, assumptions, tolerances, and gate outcomes |
| Any figure | Must carry figure_provenance linking to its ClaimRecord |

---

## 6. Geometry Adapter Doctrine

This section governs how any physical realization connects to the frozen control language. It is the bridge between theorem-space and hardware-space.

### Principles

1. **Physical realizations do not alter the frozen control language.** M, G, D, and all Layer A identities are properties of the K₄ graph. They hold regardless of whether the tetrahedron is made of copper wire, PCB traces, or spaghetti.

2. **Every physical realization must map to canonical edge-current coordinates.** The adapter produces a GeometryAdapterResult that expresses the physical system in the frozen (w, u_coil, u) basis. The exploration engine never sees raw hardware parameters — only frozen coordinates.

3. **Adapter outputs must declare their approximation class and symmetry deviations.** A GeometryAdapterResult must state: what symmetry class the realization belongs to (Td_regular, irregular, degenerate), which frozen assumptions are broken, preserved, or only approximately inherited, and the resulting claim_ceiling.

4. **What always holds vs what changes under non-ideal geometry:**

| Always holds (graph theory) | Changes (physical embedding) |
|---|---|
| M^T · G = 0 | F₀ · G = 0 (requires T_d) |
| D · M = 0 | rank(F₀·M) = 3 (requires non-degenerate) |
| P_cycle + P_cut = I₆ | κ(F₀·M) = 2 (requires regular) |
| I = M·w + G·u (unique decomposition) | Centroid inversion formula coefficients |

5. **Non-canonical geometry must provide a calibrated F-matrix.** If the geometry is irregular, the adapter must supply an F_matrix obtained from measurement or high-fidelity simulation, not from the frozen Biot-Savart formula. The frozen formula is a model for the regular case only.

### Adapter Interface

```python
def adapt_geometry(vertex_positions: np.ndarray,  # (4,3)
                   field_model: str = "biot_savart",
                   wire_radius: float = 0.0,
                   ) -> GeometryAdapterResult:
    """
    Map a physical tetrahedron into frozen control coordinates.
    
    Returns a GeometryAdapterResult with:
    - Calibrated F0, F0M, F0M_inv
    - Symmetry classification and deviation report
    - Claim ceiling for this geometry
    """
```

### Known Geometry Classes

| Class | Example | Claim ceiling | What breaks |
|-------|---------|---------------|-------------|
| Td_regular | Ideal regular tetrahedron | [G] | Nothing — full theorem set |
| Td_approximate | Machined frame, <1% tolerance | [G] with error bounds | κ deviates from 2 |
| Irregular | Unequal edges | [M] | F₀·G ≠ 0 (small), κ variable |
| Degenerate (h→0) | Planar PCB layout | [M] | F₀·G ≈ 0, rank may drop |
| Multi-cell | Array of K₄ cells | [M] | Inter-cell coupling unmodeled |
| Bundle | Racetrack coils on edges | [M] | Biot-Savart residual grows |

---

## 7. Build Order

| Phase | Days | Deliverable | Key Action | Test |
|-------|------|-------------|------------|------|
| 0: Foundation | 1 | Unpack v3 as package, confirm 182/182 | Set up directory structure | verify_all PASS |
| 1: Core Adapter | 2–3 | context.py, signal.py, solver.py | **Remove duplicated algebra/field definitions from k4_engine.py and replace with imported canonical sources from v3** | DC command → B_error < 10⁻¹² |
| 2: Observation | 3–4 | viewports.py, observables.py | Wire 9 canonical viewports to field engine | 9 VPs for BASIC-BZ preset match regression |
| 3: Modes | 4–6 | modes.py, trajectory.py | Port 12 modes from k4_engine, add decomposition roundtrip gates | 3-freq dim=3 (non-star edges), dim=2 (star) |
| 4: Experiments | 6–8 | experiment.py, artifacts.py, report.py | Build ExperimentResult with full ClaimRecord + provenance | SELECTIVITY_PROFILE crossover ≈ 0.5L |
| 5: Visualization | 8–10 | figures.py, panels.py | Merge v3 diagnostics + engine viewports | 8 v3-style figures generate cleanly |
| 6: Governance | 10 | Wire verify_all + policy + assumptions + import enforcement | Add import-time assertions preventing v2 or circular imports | 7 canonical presets all certify |

---

## 8. Research Experiments (First 5)

### Experiment 1: Selectivity Crossover Surface

**Question:** Complete 3D shape of the cycle→cut crossover surface.

**Observable:** Selectivity ratio |B_cycle|/|B_cut| at (r, θ, φ) for unit cycle + unit cut excitation.

**Method:** Radial scan along 200+ directions (Lebedev quadrature on S²), find r_cross(θ,φ) where selectivity = 1, reconstruct surface.

**Pass/fail:** Surface reconstructs as a closed, smooth tetrahedral deformation of a sphere. Known regression anchors: r_cross ≈ 0.31L (face axis), 0.70L (vertex axis), anisotropy ratio 2.4:1 ± 5%.

**Current claim:** [M]. **Upgrade path to [G]:** Derive crossover surface analytically from the F(r)·M and F(r)·G eigenvalue structure using T_d symmetry constraints.

**Value:** Maps cycle-authority vs cut-authority boundary. Essential for any application exploiting the r⁻² channel.

### Experiment 2: AC Orbit Zoo with Config Pairs

**Question:** Complete map of B-tip orbit shapes from config-pair drives at various frequency ratios.

**Observable:** SVD singular value ratios of B(t) trajectory, eccentricity, volume fill fraction.

**Method:** 6 config pairs × 10 frequency ratios (1:1 through φ:1) × SVD dimensionality. Each trajectory: 2000 samples over 20 cycles.

**Pass/fail:** Config 0+1 at incommensurate ω reproduces SV [1.00, 0.76±0.05, 0.31±0.05]. All same-frequency pairs give dim ≤ 2. All incommensurate cross-config pairs give dim = 3.

**Current claim:** [G] (exact centroid field, regular K₄). **Upgrade path:** Already at ceiling for centroid cycle-only field. No upgrade needed — but the orbit catalog itself is [M] (specific parameter choices).

**Value:** Defines achievable time-domain B patterns at centroid. Directly relevant to Lissajous display, MHD stirring.

### Experiment 3: Null Placement Cost Landscape

**Question:** Full 3D effort map for null placement inside the tetrahedron.

**Observable:** Effort = max(|I_edge|), condition number κ(F(r)), B preservation at centroid after null imposed.

**Method:** 500+ interior points (tetrahedral grid), minimum-norm solve at each, record effort + κ + B_centroid preservation.

**Pass/fail:** Effort varies ≤ 3:1 inside 0.2L sphere. Known anchor: 2:1 variation around 0.1L orbit. Nulls at centroid cost = 0 (exact). All interior nulls are true nulls (positive-definite Hessian), not saddle nulls.

**Current claim:** [M]. **Upgrade path to [G]:** Prove ker(F(r)) dimensionality ≥ 3 for all interior points via T_d-equivariant argument.

**Value:** Practical null-placement capability map. Essential for levitation and trapping applications.

### Experiment 4: Multipole Selection Rule Verification

**Question:** Is cycle→{l=1,2}, cut→{l≥3} a theorem or numerical observation?

**Observable:** Multipole power P(l) by order l for each of the 6 basis vectors (3 cycle, 3 cut). Transfer matrix singular values per (channel, l).

**Method:** All 6 basis vectors, spherical harmonic decomposition at r = 2L, 3L, 5L. Compute forbidden/allowed power ratio.

**Pass/fail:** Forbidden orders have power < 10⁻²⁰ (machine noise). Allowed orders have power > 10⁻¹⁴. Separation ratio > 10⁶ for all basis vectors at all radii.

**Current claim:** [M] (numerical observation only). **Upgrade path to [A]:** Prove via T_d representation theory that cycle modes (T₂ irrep) couple only to l ≤ 2 spherical harmonics, and cut modes (T₁ irrep) have vanishing l ≤ 2 coupling by Wigner-Eckart selection rule.

**Value:** If proven as theorem, this is the far-field decoupling result: cycle and cut are separated across the entire multipole expansion through l=2.

### Experiment 5: Impedance Block-Diagonality vs Frequency

**Question:** At what frequency does the Hodge decoupling of impedance break down?

**Observable:** ‖M^T·Z(ω)·G‖ / ‖Z(ω)‖ (normalized leakage) as function of frequency.

**Method:** Z(ω) from inductance module at 50 log-spaced frequencies from 1 Hz to 10 MHz. Record leakage norm, impedance eigenvalue spectrum.

**Pass/fail:** Leakage < 10⁻¹⁰ for f < f_quasi_static. Identify f where leakage exceeds 1% and 10%.

**Current claim:** [G*] (full-wave model, no capacitance/skin/Duffy). **Upgrade path to [G]:** Add capacitance matrix and skin-effect correction; if decoupling persists, promote.

**Value:** Defines operational frequency ceiling for Hodge decoupling guarantee.

---

## 9. Risks and Unresolved Tensions

### Architecture Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| k4_engine.py has divergent matrix copies | HIGH | Phase 1: remove and replace with v3 imports |
| v2/v3 coexistence | MEDIUM | Archive v2, declare v3 canonical, never import v2 at runtime |
| 27-param signal layer ungated | MEDIUM | Phase 3: add decomposition roundtrip gates |
| Regression baseline drift | LOW | v3 verify_all as mandatory startup gate |
| Circular import between exploration and frozen layers | MEDIUM | Import rules (§3) + CI enforcement |

### Mathematical Tensions

| Tension | Status | Impact |
|---------|--------|--------|
| ζ₄ = 1/7: rep theory or coincidence? | OPEN [C] | Large body of results conditional on this |
| Multipole selection rule: theorem? | OPEN [M] → [A] path identified | Would extend separation to entire far field |
| Full-wave: no capacitance, skin, Duffy | Known limit of [G*] | All full-wave results capped at [G*] |
| 9K₁ = 7J₀: is 7 = dark line count? | OPEN [C] | Would connect frame bound to kernel |

### Integration Traps

| Trap | Prevention |
|------|------------|
| Floating SymPy (Float vs Integer) | All gates check isinstance(result, Integer) |
| Edge ordering mismatch | Single canonical ordering from v3 truth_kernel |
| Ad hoc vertex construction | Always use make_vertices(L) from v3 field_engine |
| Config D assumption leak | policy.enforce_config_contract before E/B claims |
| "Exact at centroid" → "exact everywhere" | Every off-centroid claim must be [M] or justified |
| Breathing direction = [1,1,1] for all configs | Use config-specific vectors from Mar 7 correction |
| Visualization computing theorem-class quantities | Import rules: viz layer consumes artifacts, never computes [A]/[G] |

---

## Appendix A: Chat-Mined Results Not in Any Frozen Module

| Result | Session | Claim | Target | Upgrade Path |
|--------|---------|-------|--------|-------------|
| 4 config transverse planes, 3D orbit proof | Mar 7 | [G] | trajectory.py | At ceiling |
| Config 0: E leads B by 60° structural offset | Mar 7 | [G] | modes.py | Prove from S matrix structure |
| Selectivity surface anisotropy 2.4:1 | Feb 26 | [M] | observables.py | → [G] via analytic F(r) argument |
| 5-zone spatial regime map | Feb 26 | [H] | viewports.py | → [M] via systematic scan |
| Null orbit cost 2:1 variation at 0.1L | Mar 3 | [M] | experiment.py | → [G] via ker(F(r)) analysis |
| E_INDESTRUCTIBLE (E exact under B overconstraint) | Mar 3 | [A] | presets | Already at ceiling |
| Multipole transfer matrix 10⁶ separation | Mar 3 | [M] | Experiment 4 | → [A] via selection rule proof |
| Centroid cost isotropy S·Gram⁻¹·Sᵀ = I₃ | Mar 3 | [G] SymPy | truth_kernel ext | At ceiling |
| Null = 4 needles, 111:1 anisotropy | Mar 3 | [M] | null_tet ext | → [G] via T_d orbit analysis |
| 2-point B: rank-5 on symmetry axes | Mar 3 | [M] | solver.py | → [G] via equivariance |
| Cut dead zone: 226:1 toward V_{k+1} | Mar 3 | [M] | observables.py | → [G] via cut basis structure |
| Cycle-only suffices to 50% vertex distance | Mar 3 | [H] | solver heuristic | → [M] via systematic scan |
| Wigner-Eckart amplitudes for ζ₄ | Mar 1 | [A]+[G] | commutant ext | At ceiling |
| MHD flow: 1-in, 3-out + face return | Mar 7 | [H] | extensions | → [M] via CFD |
| RC submersible spec ($250–400) | Mar 7 | [H] | hardware roadmap | → [H] validated via build |

---

## Appendix B: Session Doctrine Quick Reference

| Class | Definition | Example |
|-------|-----------|---------|
| **Proven** | Integer(0) via SymPy, or algebraic theorem | M^T·G = 0 |
| **Derived but Unverified** | Follows logically from proven core, not yet tested or formally proved | Multipole selection rule as theorem |
| **Engineering Heuristic** | Useful approximation or design rule, not a theorem | "Pure cycle suffices to 50% vertex distance" |
| **Speculative** | Conceptual or visionary, not mapped to variables or observables | K4 stellarator, volumetric maglev grid |

No response in this engine should blur these categories.
