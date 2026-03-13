# K4 RECIPES
## Integration Patterns & Extension Points

**For:** Developers, researchers, and future AI sessions working with `k4_frozen_v3/`  
**Assumes:** You've read `REFERENCE.md` and run `python -m k4_frozen_v3.verify_all`

---

## How to Read This

The frozen stack is a **bar of spirits.** This document is the **cocktail menu.**

Each recipe shows:
- **What you're making** (the drink)
- **What you need** (the ingredients from `k4_frozen_v3/`)
- **The steps** (code pattern)
- **The claim class** (how strong is this drink?)

---

## Recipe 1: Basic Field Computation

**Goal:** Compute B at the centroid for a target field.

```python
import numpy as np
from k4_frozen_v3 import centroid_inversion, M, G, make_vertices, field_at_centroid

# Your target
B_target = np.array([0.0, 0.0, 1e-6])  # 1 µT in z

# Inversion (exact at centroid) [G]
w = centroid_inversion(B_target, L=0.1)

# Total current (with free cut component)
u_coil = np.zeros(3)  # no cut excitation
I = M.astype(float) @ w + G.astype(float) @ u_coil

# Verify
V = make_vertices(0.1)
F0 = field_at_centroid(V)
B_achieved = F0 @ I
print(f"Target:   {B_target}")
print(f"Achieved: {B_achieved}")
print(f"Error:    {np.linalg.norm(B_target - B_achieved):.2e}")
```

**Claim class:** [G] — exact for regular K₄ + Biot-Savart + centroid.

---

## Recipe 2: Certified Session

**Goal:** Compile a session that passes all regression tests and policy.

```python
from k4_frozen_v3 import solve_session, run_regression, print_regression
from k4_frozen_v3.policy import gate, CANONICAL_K4
from k4_frozen_v3.session_schema import SessionResult, ClaimClass, ConfigID

# Compile
session = solve_session(
    name="MY_SESSION",
    description="Custom B+E target with null placement",
    B_target=np.array([0, 0, 1e-6]),
    E_target=np.array([100, 0, 0]),
    null_point=np.array([0.01, 0, 0]),
    L=0.1,
    config=ConfigID.D,
)

# The session already ran all 12 regression tests
print(f"Regression: {session['regression_summary']['status']}")
print(f"Tier: {session['diagnostics']['tier']}")
```

**Null placement note:** `solve_session` places nulls in the full 6-edge
current space (6 DOF). Cycle-only steering (3 DOF via `M·w`) cannot create
nontrivial off-centroid nulls when `F(r)·M` is invertible — you need the
cut degrees of freedom.

# For individual results, use the policy gate
result = SessionResult(
    description="Custom off-centroid measurement",
    claim_class=ClaimClass.G,  # will be auto-downgraded if needed
    observation_class=ObservationClass.FACE_CENTER,
    # ... other fields
)
result = gate(result, geometry=CANONICAL_K4)
# result.claim_class is now [M] (auto-downgraded by policy)
```

**Pattern:** Always use `gate()` for new results. It auto-downgrades
claims that exceed their ceiling and catches config violations.

---

## Recipe 3: Non-Ideal Geometry

**Goal:** Use the K₄ framework with an irregular tetrahedron.

```python
from k4_frozen_v3 import M, G, decompose_current
from k4_frozen_v3.policy import GeometryCertification
from k4_frozen_v3.integration import CalibratedFieldMatrix
from k4_frozen_v3.session_schema import ConfigID

# Step 1: Certify your geometry
my_geo = GeometryCertification(
    name="Squashed prototype v1",
    description="Tetrahedron with 10% edge length variation",
    vertex_count=4,
    edge_count=6,
    is_complete_graph=True,
    vertex_connectivity_realized=True,
    kcl_enforced=False,
    config_id=ConfigID.D,
    geometry_type="irregular_K4",
    deviations=["Edge lengths vary ±10%", "V0 shifted 5mm"],
    calibration_required=True,  # MUST be True for non-regular
)

# Step 2: Validate the certification
warnings = my_geo.validate()
print(f"Max claim class: [{my_geo.max_claim_class().value}]")
# Will print [M] — irregular geometry caps everything

# Step 3: Provide calibrated F matrix (from FEM or measurement)
F_measured = my_fem_solver.compute_field_matrix(my_vertices, centroid)
cal_F = CalibratedFieldMatrix(
    description="FEM field matrix at centroid",
    geometry_cert=my_geo,
    F_matrix=F_measured,
    evaluation_point=centroid,
    source="comsol",
    b_model_tier=BModelTier.FINITE_SEGMENT_BIOT_SAVART,
)

# Step 4: Check diagnostics
diag = cal_F.diagnostics()
print(f"‖F·G‖ = {diag['norm_FG']:.2e}")  # Won't be zero!
print(f"κ(F·M) = {diag['kappa_FM']:.2f}")  # Won't be 2.0!

# Step 5: The algebra STILL WORKS
# M, G, D, decompose_current — all still valid
# Only the field interpretation changes
I_total = my_computed_currents
I_cyc, I_cut, w, u = decompose_current(I_total)
# w and u are still exact — the decomposition is Layer 1
```

**Key insight:** M^T·G = 0 holds regardless. The decomposition is always
valid. What changes is the *meaning* of that decomposition in field terms.

---

## Recipe 4: Multi-Cell Array

**Goal:** Superimpose fields from multiple K₄ cells.

```python
from k4_frozen_v3.integration import K4Cell, K4Array
from k4_frozen_v3 import make_vertices, M, G
from k4_frozen_v3.policy import GeometryCertification
from k4_frozen_v3.session_schema import ConfigID

# Build an array of two cells
V1 = make_vertices(L=0.1)  # cell at origin
V2 = make_vertices(L=0.1)
V2 += np.array([0.12, 0, 0])  # shifted in x

array = K4Array(coupling_model="superposition")
array.add_cell(K4Cell("cell_A", V1, config_id=ConfigID.D))
array.add_cell(K4Cell("cell_B", V2, config_id=ConfigID.D))

# Each cell has its OWN w and u_coil
w_A = centroid_inversion(np.array([0, 0, 1e-6]), L=0.1)
w_B = centroid_inversion(np.array([0, 0, -1e-6]), L=0.1)

currents = {
    "cell_A": M.astype(float) @ w_A,
    "cell_B": M.astype(float) @ w_B,
}

# Total field at any point is superposition
r_probe = np.array([0.06, 0, 0])  # between the cells
B_total = array.total_field_at(r_probe, currents)
print(f"B at midpoint: {B_total}")

# CLAIM CLASS: [M] — superposition ignores mutual inductance
```

**Warning:** Superposition is approximate. Real multi-cell systems
have mutual inductance between coils in different cells. This requires
Neumann integral computation — not included in the frozen stack.

---

## Recipe 5: The Null Tetrahedron (Spatial Field Sculpting)

**Goal:** Use cut-space freedom to place a field null.

```python
from k4_frozen_v3 import (
    centroid_inversion, M, G, make_vertices,
    field_matrix, field_at_centroid, compute_null_direction,
    FACE_NULL_DIRECTIONS
)

V = make_vertices(0.1)
F0 = field_at_centroid(V)

# Step 1: Set centroid B target
B_target = np.array([0, 0, 1e-6])
w = centroid_inversion(B_target, L=0.1)

# Step 2: Use cut DOF to place a null at r_null
r_null = np.array([0.01, 0, 0])
F_null = field_matrix(r_null, V)

# The cut component must cancel the cycle leakage at r_null
# F_null · (M·w + G·u) = 0  →  F_null·G·u = -F_null·M·w
FG_null = F_null @ G.astype(float)
FM_w = F_null @ M.astype(float) @ w
u_coil = -np.linalg.lstsq(FG_null, FM_w, rcond=None)[0]

# Verify
I = M.astype(float) @ w + G.astype(float) @ u_coil
B_at_null = F_null @ I
B_at_cent = F0 @ I
print(f"B at centroid: {np.linalg.norm(B_at_cent)*1e6:.3f} µT")
print(f"B at null:     {np.linalg.norm(B_at_null)*1e6:.6f} µT")

# Check which face null direction we're near
null_dir, depth = compute_null_direction(r_null, V)
print(f"Null direction: {null_dir}")
print(f"Null depth: {depth:.4f}")
```

**The null tetrahedron tells you:** If you're near face F₀, the invisible
direction is [1,1,1]. Near F₁, it's [1,0,0]. These SNAP — they don't
interpolate on symmetry paths. Only the depth changes continuously.

---

## Recipe 6: Policy-Gated Extension Development

**Goal:** Build a new analysis (say, inductance matrix) that respects policy.

```python
from k4_frozen_v3.policy import gate, enforce_all, GeometryCertification, CANONICAL_K4
from k4_frozen_v3.session_schema import (
    SessionResult, SessionBundle, ConfigID, BModelTier,
    ClaimClass, ObservationClass, Normalization, PassFail
)

# Create a session bundle
session = SessionBundle(
    session_id="2026-02-27-inductance",
    session_date="2026-02-27",
    description="Mutual inductance matrix computation",
)

# Every result goes through the gate
result = SessionResult(
    description="Mutual inductance L_01_23",
    config_id=ConfigID.D,
    b_model_tier=BModelTier.FINITE_SEGMENT_BIOT_SAVART,
    claim_class=ClaimClass.G,  # WRONG — inductance is model-dependent
    observation_class=ObservationClass.CUSTOM,
    quantity_name="mutual_inductance_01_23",
    normalization=Normalization.SI_PHYSICAL,
    value=1.23e-9,
    status=PassFail.PASS,
)

# The gate catches the overclaim and auto-downgrades
result = gate(result, geometry=CANONICAL_K4)
# result.claim_class is now [M] (gate enforced the ceiling)

session.add(result)
print(session.summary())
```

**Pattern:** Develop first, gate last. The policy module is the final
quality check, not a development obstacle.

---

## Recipe 7: Patent Claim Evidence

**Goal:** Map a session's results to the 14 patent claims.

The 14 claims (from K4 Definitive Reference §8.1):

```
Category A: Structural Architecture
  A1: K₄ eigenspace dimensionality         [PROVEN]
  A2: Unique cycle+cut decomposition        [PROVEN: det([M|G])=±16]
  A3: Cut annihilation F₀·G=0              [PROVEN: Integer(0)]
  A4: Cycle spanning rank(F₀·M)=3          [PROVEN: det=4096√6/9L³]

Category B: Independent E/B Control
  B1: E and B independent                   [STRUCTURAL]
  B2: E uniform inside tetrahedron          [ANALYTIC]
  B3: E×B fully programmable               [DERIVED]

Category C: Spatial B-Field Sculpting
  C1: Interior nulls placeable              [NUMERICAL: 36-pt ring]
  C2: Cut-coil monopole-like far-field      [NUMERICAL: 23-pt scan]
  C3: Up to 9 simultaneous observables      [STRUCTURAL+NUMERICAL]

Category D: Hardware Architecture
  D1: H-bridges recover cut space           [STRUCTURAL]
  D2: Frequency separation → indep E+B      [STRUCTURAL]

Category E: Diagnostic/Certification
  E1: Tier system graceful degradation       [STRUCTURAL+NUMERICAL]
  E2: Principal angles predict degradation   [NUMERICAL]
```

Every session in the canonical library maps to specific claims via
the cross-reference matrix. To add evidence for a claim:

```python
# Compile a session that exercises the claim
session = solve_session(
    name="NULL_ORBIT_RING",
    description="36-point null ring for claim C1",
    B_target=np.array([0, 0, 1e-6]),
    null_point=np.array([0.01, 0, 0]),
)

# Check regression (all 12 tests must pass)
assert session['regression_summary']['status'] == 'PASS'

# The margin and effort are the evidence
print(f"Margin: {session['diagnostics']['margin']:.4f}")
print(f"Max current: {session['diagnostics']['max_current_A']:.1f} A")
```

---

## Recipe 8: Hierarchical Integration (Hyper-recipes)

**Goal:** Compose K₄ cells into larger structures.

### 8a. Planar Array (2D)

Project each K₄ cell onto a shared plane. Vertices are shared between
adjacent cells. Each cell retains its own M, G decomposition, but
shared vertices create coupling constraints.

```
   V₀───V₁    V₁───V₄
   │╲  ╱│     │╲  ╱│
   │ V₂ │     │ V₅ │
   │╱  ╲│     │╱  ╲│
   V₃───V₁    V₁───V₆
   Cell A      Cell B  (V₁ shared)
```

**Rule:** Shared vertices enforce current conservation across cells.
This is an inter-cell KCL constraint, not covered by the per-cell
incidence matrix D. Model it as an additional constraint row.

### 8b. Hierarchical Energy Transfer

A large-scale K₄ cell whose "edges" are themselves smaller K₄ cells.
The outer cell provides the low-frequency envelope; inner cells provide
the high-frequency modulation.

**Frequency separation:** Inner cells operate at f_inner >> f_outer.
The outer cell sees time-averaged fields from inner cells. Inner cells
see quasi-static fields from the outer cell.

### 8c. Toroidal Closure

Wrap a 1D chain of K₄ cells into a torus. The first and last cells
share vertices, creating a topological constraint.

**All hierarchical recipes are [H] claim class** — they depend on
specific hardware choices and inter-cell coupling models.

---

## Recipe 9: Visualization & Diagnostics

**Goal:** Generate diagnostic plots from session data.

```python
from k4_frozen_v3 import (
    make_vertices, field_matrix, field_at_centroid,
    M, G, face_centers, edge_midpoints, centroid_inversion,
    decompose_current
)

# Selectivity radial profile
V = make_vertices(0.1)
w = centroid_inversion(np.array([0, 0, 1e-6]))
I_cyc = M.astype(float) @ w
I_cut = G.astype(float) @ np.array([1, 0, 0])  # example cut

r_values = np.linspace(0.001, 0.05, 50)
selectivity = []
for r in r_values:
    point = np.array([r, 0, 0])
    F = field_matrix(point, V)
    B_cyc = np.linalg.norm(F @ I_cyc)
    B_cut = np.linalg.norm(F @ I_cut)
    selectivity.append(B_cyc / B_cut if B_cut > 1e-30 else float('inf'))

# Plot with matplotlib, plotly, etc.
# Label: "[G] on C₃ axis, [M] interpolated off-axis"
```

---

## Operator Workflow: Target → Verified Artifact

Every control task follows this path:

```
1. SPECIFY: What fields do you want?
   B_target = [0, 0, 1e-6]    # 1 μT in z
   E_target = [100, 0, 0]     # 100 V/m in x
   null_point = [0.01, 0, 0]  # null at 0.1L offset

2. CLASSIFY: Which tier are you in?
   B + E at centroid → Tier 1 (always exact)
   + one null point  → Tier 2 (uses 3 cut DOF)
   + second B target → Tier 3 (least-squares)

3. SOLVE: Build constraint matrix, apply SVD
   from k4_frozen_v3 import centroid_inversion, e_field_volume_matrix
   w = centroid_inversion(B_target)
   u = np.linalg.solve(E_vol, E_target)
   # For null: stack [F0@M, F0@G; Fn@M, Fn@G] and lstsq

4. VERIFY: Check every target was hit
   B_achieved = F0 @ (M @ w + G @ u_coil)
   E_achieved = E_vol @ u
   B_at_null  = F_null @ I_edge
   # Print errors. If > 1e-6: investigate.

5. CERTIFY: What claim class does this earn?
   from k4_frozen_v3 import gate
   gate('centroid', 'regular', B_error)  # enforces ceiling
```

Do NOT skip step 4. The solver always produces numbers; only
verification tells you whether those numbers mean anything.

---

## Assumptions / Regime Matrix

Which modules are valid under which physical conditions:

| Module | Geometry | Frequency | Conductor | E-field |
|--------|----------|-----------|-----------|---------|
| truth_kernel | ANY K₄ | ANY | ANY | N/A |
| field_engine | Regular tet | DC (static) | Thin wire, full-span | Point electrodes |
| inductance | Regular tet | DC to f_3dB | Thin wire, finite radius | N/A |
| full_wave | Regular tet | DC to η≈1 | Thin wire, no skin effect | No capacitance |
| commutant | Regular tet | ANY (structural) | ANY (gradient only) | N/A |
| ring_quiet | ANY K₄ | ANY | ANY | N/A |
| bose_mesner | Regular tet | DC | Thin wire | N/A |
| e_field_volume | Regular tet | DC | N/A | Point, uniform interior |

**What breaks where:**
- Irregular geometry: truth_kernel still exact; field_engine needs calibrated F
- High frequency (η>1): full_wave Z values unreliable, structural decoupling still holds
- Thick conductors: field_engine centroid theorems approximate, calibrate
- Finite electrodes: E-field non-uniform near vertices, model breaks at boundary

---

## Worked Examples: v3 Branches

### Full-Wave: Verify Hodge-Impedance Decoupling

```python
from k4_frozen_v3.full_wave import compute_impedance_matrix, analyze_impedance
import numpy as np

L = 0.1  # 10 cm tetrahedron
c = 3e8
edge_len = L * np.sqrt(2)

for eta in [0.1, 1.0, 5.0]:
    omega = eta * c / edge_len
    Z = compute_impedance_matrix(L, omega, n_quad=32)
    result = analyze_impedance(Z, eta)
    print(f"η={eta:.1f}: cross-coupling = {result.cross_coupling:.2e}")
    # Should be < 1e-14 at all frequencies

# CAUTION: Z values at η>1 are structurally correct (decoupled)
# but numerically incomplete (no capacitance, no skin effect).
```

### Commutant: Compute ζ₄ and Check 2-Design

```python
from k4_frozen_v3.commutant import compute_zeta4, verify_projective_2design

zeta = compute_zeta4()
print(f"ζ₄ = {zeta:.8f}  (should be 1/7 = {1/7:.8f})")
# This is a numerical cross-check (~1e-4 accuracy from finite differences).
# The algebraic proof: 9K₁ = 7J₀ from IBP identity → ζ₄ = 1/7 exactly.

design_ok = verify_projective_2design(verbose=True)
# Verifies that the 7 T_d axes form a projective 2-design: Σ P_d = (7/3)·I₃
```

### Ring-Quiet: Silence a Face

```python
from k4_frozen_v3.ring_quiet import compute_ring_quiet, canonical_vortex_mode
from k4_frozen_v3 import EDGE_LABELS
import numpy as np

# Canonical mode: w = [1, -0.5, -0.5] (balanced: sum = 0)
sol = canonical_vortex_mode()

print("Edge currents:")
for k, label in enumerate(EDGE_LABELS):
    status = "SILENT" if abs(sol.I_edge[k]) < 1e-10 else "ACTIVE"
    print(f"  {label}: {sol.I_edge[k]:+8.4f} A  [{status}]")
print(f"|B| at centroid: {np.linalg.norm(sol.B_centroid)*1e6:.1f} μT")

# Any balanced w works. Try your own:
sol2 = compute_ring_quiet(np.array([2.0, -1.0, -1.0]))
# Ring edges E12, E13, E23 are exactly zero — algebraic identity.
# CAUTION: minimum-norm lstsq assumes V₀=0 gauge. If hardware
# uses different ground, add explicit gauge constraint.
```

### Simultaneous B + E + Null (Tier 1+2 Hero Scenario)

```python
from k4_frozen_v3 import (
    M, G, EDGE_LABELS, make_vertices,
    field_at_centroid, e_field_volume_matrix, centroid_inversion,
    field_matrix,
)
import numpy as np

V = make_vertices(0.1)
F0 = field_at_centroid(V)
E_vol = e_field_volume_matrix(V)
Mf, Gf = M.astype(float), G.astype(float)

# Targets
B_tgt = np.array([0, 0, 1e-6])    # 1 μT in z
E_tgt = np.array([100, 0, 0])     # 100 V/m in x
null_pt = np.array([0.01, 0, 0])  # 0.1L offset

# Solve B + null (Tier 1+2): stacked constraint
FM, FG = F0 @ Mf, F0 @ Gf
F_null = field_matrix(null_pt, V)
C = np.vstack([np.hstack([FM, FG]),
               np.hstack([F_null @ Mf, F_null @ Gf])])
b = np.concatenate([B_tgt, np.zeros(3)])
x, _, rank, sv = np.linalg.lstsq(C, b, rcond=None)
w, u_coil = x[:3], x[3:]

# Solve E (independent channel)
u = np.linalg.solve(E_vol, E_tgt)

# Verify ALL targets
I_edge = Mf @ w + Gf @ u_coil
B_ach = F0 @ I_edge
B_null = F_null @ I_edge
E_ach = E_vol @ u

print(f"B centroid error: {np.linalg.norm(B_ach - B_tgt):.2e} T")
print(f"|B| at null:     {np.linalg.norm(B_null):.2e} T")
print(f"E error:         {np.linalg.norm(E_ach - E_tgt):.2e} V/m")
# B and E are structurally independent. E is NEVER compromised
# by any B constraint — separate hardware channels.
```

---

## What Doesn't Belong Here

These things should NOT be added without careful policy review:

- **Plasma coupling** (MHD interaction with K₄ fields, [H])
- **Consciousness/E8/quantum** connections (interpretive [C], not operational)
- **φ (golden ratio)** — does NOT appear in regular K₄ arithmetic

Note: Inductance (inductance.py) and full-wave impedance (full_wave.py)
were previously excluded but have been admitted as classified modules
with explicit regime limitations and claim class ceilings. They went
through the process below and carry [G] structural / [M] numerical claims.

If you want to add new topics:
1. Create a separate module (don't modify frozen files)
2. Import from `k4_frozen_v3` (don't copy/paste)
3. Get a GeometryCertification
4. Gate every result through `policy.gate()`
5. Accept the claim class ceiling

---

## Module Map

| Module | Layer | Tests | What it gives you |
|--------|-------|-------|------------------|
| `truth_kernel` | 0-1 | 27 integer + 12 SymPy | M, G, D, projectors, decomposition |
| `field_engine` | 3-4 | 10 model tests | F₀, E_vol, centroid inversion |
| `symbolic_proofs` | 3-4 | 15 exact proofs | F₀·G=0, det(F₀M), eigenvalues |
| `null_tetrahedron` | — | 15 tests | Face nulls, sufficiency, edge nulls |
| `full_wave` | 4W | 12 tests | Z(ω), Hodge-impedance decoupling |
| `commutant` | S4 | 5 tests | Σ eigenvalues, ζ₄=1/7, 2-design |
| `ring_quiet` | Control | 6 tests | Algebraic ring-edge cancellation |
| `bose_mesner` | 5 | 9 tests | {αI+βJ} algebra, spectral κ |
| `spherical_harmonics` | 6 | 9 tests | 3-phase, mode decomposition |
| `sphere_sculpt` | 7 | 9 tests | Energy-normalized sculpting |
| `session_compiler` | — | 12 regression | Solver, tier system, presets |
| `inductance` | 4+ | 9 tests | L tensor, Hodge decoupling, control |
| `policy` | — | 6 contract tests | Claim ceiling, config gates |
| `integration` | — | Checklist | Non-ideal mapping, multi-cell |
| `assumptions` | — | Preflight | Regime validation, ledger |
| `diagnostics` | — | Visual | Plot generation (manual inspection) |

**Total: 176 consistency checks across 15 verified sections.**

---

*End of K4 Recipes v3.0.0*
