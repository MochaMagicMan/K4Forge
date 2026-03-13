# GEOMETRY INTEGRATION SPEC (CORRECTED)
## Physical Realizations → Frozen Control Coordinates

---

## 1. THE CORE PRINCIPLE

The frozen truth kernel (M, G, D) is a property of the K4 GRAPH.
It holds regardless of physical geometry.

What changes with geometry:
- F(r) — the 3×6 field matrix at point r
- F₀·G — zero only for T_d-symmetric geometries at the centroid
- κ(F₀·M) — equals 2 only for regular tetrahedron
- The centroid inversion formula coefficients

The adapter's job: given a physical realization, compute F(r) correctly
and report what assumptions hold/break.

---

## 2. EDGE GEOMETRY MODELS

### ⚠ CRITICAL NOTE ON RACETRACK COILS

The racetrack/converge-expand coil concept was explored extensively in
Jan-Feb 2026 across multiple sessions. **The geometry was never
successfully modeled.** Every attempt produced separate concentric
ovals instead of the actual continuous spiral wire path. The concept
is physically sound (coil plane containing edge + centroid direction
preserves F·G = 0) but no correct parametric model or visualization
was ever achieved.

**DO NOT IMPLEMENT racetrack coil geometry in the engine.**
It remains a future hardware R&D concept only. The Biot-Savart
numbers quoted for racetrack performance (1.3×, 91.5% alignment)
were computed from the WRONG geometry (separate ovals, not a spiral)
and should not be cited.

### 2.1 Single Filament Wire (baseline model)

The mathematical ideal. Each edge is one infinitely thin wire from
V_i to V_j. This is what ALL proven results use.

- Field: Biot-Savart finite segment formula (field_engine.py)
- F·G = 0: exact at centroid for regular K4
- Claim: [G]
- This is the ONLY model validated by the frozen core

```python
# Already implemented in k4_frozen/field_engine.py:
B = biot_savart_segment(P1, P2, r, I=1.0)
```

### 2.2 Bundled Parallel Wire (preferred multi-turn, IMPLEMENT THIS)

N wires running the SAME straight path from V_i to V_j, bundled
together with small transverse offsets.

This is the simplest honest multi-turn model:
- Same geometry as single wire, just N copies with slight offset
- F·G = 0 preserved EXACTLY (same field direction, scaled magnitude)
- Field scales as approximately N × single wire (exact for zero offset)
- Physically trivial to build: bundle of magnet wire zip-tied to frame edge
- No new field computation needed for the zero-offset limit

For finite bundle radius r_bundle:
- Each wire is offset from the edge centerline by some (dx, dy)
- The offsets break perfect T_d symmetry slightly
- F·G ≈ 0 with error proportional to (r_bundle / L)²
- Claim: [G] for zero offset, [M] for finite bundle radius

```python
def generate_bundle_segments(V_i, V_j, N_wires, r_bundle=0.0):
    """
    Generate segment list for N parallel wires bundled along edge.

    If r_bundle = 0: all wires coincide (equivalent to N×I single wire).
    If r_bundle > 0: wires distributed in a circle of radius r_bundle
    around the edge centerline.

    Returns: List[(P1, P2)] — one segment per wire.
    """
    if r_bundle <= 0 or N_wires <= 1:
        return [(V_i, V_j)] * N_wires

    edge = V_j - V_i
    edge_hat = edge / np.linalg.norm(edge)

    # Build transverse frame
    up = np.array([0., 0., 1.])
    if abs(np.dot(edge_hat, up)) > 0.9:
        up = np.array([0., 1., 0.])
    u = np.cross(edge_hat, up)
    u = u / np.linalg.norm(u)
    v = np.cross(edge_hat, u)

    segments = []
    for k in range(N_wires):
        theta = 2 * np.pi * k / N_wires
        offset = r_bundle * (np.cos(theta) * u + np.sin(theta) * v)
        segments.append((V_i + offset, V_j + offset))

    return segments
```

**Hardware build:** For L=500mm first prototype, use 20-24 AWG magnet
wire. Bundle 5-20 wires with heat shrink or zip ties along each edge
of a 3D-printed or aluminum frame. Each wire in the bundle carries
the same current (wired in series or parallel depending on driver).

### 2.3 Solenoid with Adjustable Spacing (for exploration)

N helical turns wound around the edge axis, with variable pitch
(turn spacing). This is the model for exploring how winding density
affects the field structure.

Key physics: a helix around the edge axis produces BOTH:
  - Transport current contribution (wire going from V_i to V_j) → cycle-like
  - Helical contribution (circular loops) → solenoid-like, B parallel to edge

The balance between these two depends on winding density:
  - Loose spacing (large pitch): mostly transport current, wire-like behavior
  - Tight spacing (small pitch): mostly solenoid, B parallel to edge
  - This is a CONTINUOUS transition, not a binary switch

**F·G = 0 behavior:** Degrades continuously as spacing tightens.
Loose solenoid approximately preserves F·G ≈ 0. Tight solenoid
breaks it significantly because B becomes parallel to edge axis.

**Feb 2026 session result (helix reality check):**
- Transport current (cycle channel) is INVARIANT with winding density
- Helical turns STACK on top of wire contribution, never replace it
- The transition is additive, not a tradeoff

Parameters:
  - N_turns: total number of helical turns
  - r_coil: helix radius (distance from edge centerline)
  - spacing_profile: 'uniform' or callable(t) → local pitch factor

```python
def generate_solenoid_segments(V_i, V_j, N_turns, r_coil,
                                segs_per_turn=12,
                                spacing_profile='uniform'):
    """
    Generate segments for helical winding around edge axis.

    Parameters:
        V_i, V_j: edge endpoints
        N_turns: number of helical turns (0 = straight wire)
        r_coil: helix radius
        segs_per_turn: line segments per turn (12-20 for accuracy)
        spacing_profile: 'uniform' or callable(t) -> local pitch factor
            where t in [0,1] is normalized position along edge.
            Example: lambda t: 1.0 + 2.0*abs(t - 0.5)
            gives tighter spacing at center, looser at ends.

    Returns: List[(P1, P2)] — segments for Biot-Savart.
    """
    edge = V_j - V_i
    L = np.linalg.norm(edge)
    edge_hat = edge / L

    up = np.array([0., 0., 1.])
    if abs(np.dot(edge_hat, up)) > 0.9:
        up = np.array([0., 1., 0.])
    u = np.cross(edge_hat, up)
    u = u / np.linalg.norm(u)
    v = np.cross(edge_hat, u)

    if N_turns == 0:
        return [(V_i, V_j)]

    total_segs = N_turns * segs_per_turn
    points = []

    for k in range(total_segs + 1):
        t = k / total_segs

        if spacing_profile == 'uniform' or not callable(spacing_profile):
            axial_frac = t
        else:
            # Integrate spacing profile for nonuniform pitch
            n_quad = 100
            ts = np.linspace(0, t, n_quad)
            weights = np.array([spacing_profile(ti) for ti in ts])
            cum = np.trapz(weights, ts)
            total = np.trapz(
                [spacing_profile(ti) for ti in np.linspace(0, 1, n_quad)],
                np.linspace(0, 1, n_quad)
            )
            axial_frac = cum / total if total > 0 else t

        theta = 2 * np.pi * N_turns * t
        center = V_i + axial_frac * edge
        point = center + r_coil * (np.cos(theta) * u + np.sin(theta) * v)
        points.append(point)

    return [(points[k], points[k+1]) for k in range(len(points) - 1)]
```

**Exploration use cases:**

| Spacing | N_turns | r_coil/L | Expected behavior |
|---------|---------|----------|-------------------|
| Very loose | 2-3 | 0.05 | Nearly wire-like, F·G ≈ 0 |
| Moderate | 10 | 0.03 | Mixed: transport + solenoid |
| Tight | 50+ | 0.02 | Solenoid-dominated, F·G breaks |
| Variable: tight center | 20 | 0.03 | Center-biased, interesting |
| Variable: tight ends | 20 | 0.03 | End-biased, vertex intensification |

### 2.4 Racetrack / Converge-Expand (DO NOT IMPLEMENT)

**Status: Never successfully modeled. Future hardware R&D only.**
See warning at top of section 2.

---

## 3. THE GEOMETRY ADAPTER

### 3.1 Interface

```python
class EdgeModel(str, Enum):
    FILAMENT = "filament"
    BUNDLE = "bundle"
    SOLENOID = "solenoid"
    MEASURED = "measured"


@dataclass
class EdgeRealization:
    edge_index: int
    vertex_pair: Tuple[int, int]
    model: EdgeModel
    segments: List[Tuple[np.ndarray, np.ndarray]]
    N_turns: int = 1
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class PhysicalRealization:
    vertices: np.ndarray            # (4, 3)
    edges: List[EdgeRealization]    # 6
    edge_length: float
    symmetry_class: SymmetryClass
    description: str = ""

    def field_matrix_at(self, r: np.ndarray) -> np.ndarray:
        F = np.zeros((3, 6))
        for edge_real in self.edges:
            B_unit = np.zeros(3)
            for P1, P2 in edge_real.segments:
                B_unit += biot_savart_segment(P1, P2, r, I=1.0)
            F[:, edge_real.edge_index] = B_unit
        return F

    def validate(self) -> Dict:
        c = self.vertices.mean(axis=0)
        F0 = self.field_matrix_at(c)
        G_f = G.astype(float); M_f = M.astype(float)
        FG = F0 @ G_f; FM = F0 @ M_f
        svs = np.linalg.svd(FM, compute_uv=False)
        norm_FG = float(np.linalg.norm(FG))
        return {
            "norm_FG": norm_FG,
            "rank_FM": int(np.linalg.matrix_rank(FM, tol=1e-10)),
            "kappa_FM": float(svs[0]/svs[-1]) if svs[-1] > 0 else float('inf'),
            "F0G_preserved": norm_FG < 1e-6,
            "cycle_spanning": int(np.linalg.matrix_rank(FM, tol=1e-10)) == 3,
            "claim_ceiling": (
                ClaimClass.G if norm_FG < 1e-12
                else ClaimClass.M
            ),
        }
```

### 3.2 Convenience builders

```python
EDGE_PAIRS = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]

def build_filament_realization(vertices):
    """Single wire per edge. Should match field_engine exactly."""
    ...

def build_bundle_realization(vertices, N_wires, r_bundle=0.0):
    """Bundled parallel wires."""
    ...

def build_solenoid_realization(vertices, N_turns, r_coil,
                                spacing_profile='uniform'):
    """Helical solenoid with adjustable spacing."""
    ...
```

### 3.3 FieldContext from PhysicalRealization

```python
def build_context_from_realization(real: PhysicalRealization) -> FieldContext:
    """Replaces ideal Biot-Savart with actual geometry."""
    c = real.vertices.mean(axis=0)
    F0 = real.field_matrix_at(c)
    M_f = M.astype(float); G_f = G.astype(float)
    F0M = F0 @ M_f; F0G = F0 @ G_f

    if np.linalg.matrix_rank(F0M, tol=1e-10) < 3:
        raise ValueError("rank(F0·M) < 3 — cycle spanning lost")

    F0M_inv = np.linalg.inv(F0M)
    E_vol = e_field_volume_matrix(real.vertices)
    validation = real.validate()

    return FieldContext(
        V=real.vertices, L=real.edge_length,
        F0=F0, F0M=F0M, F0M_inv=F0M_inv, F0G=F0G,
        E_vol=E_vol, M=M, G=G,
        field_matrix_at=real.field_matrix_at,
        F0G_residual=validation["norm_FG"],
        F0M_condition=validation["kappa_FM"],
        claim_ceiling=validation["claim_ceiling"],
    )
```

---

## 4. VARIABLE-APEX TETRAHEDRON

h = L√(2/3): regular. h = 0: flat/coplanar.

M^T · G = 0 holds at ALL heights (graph property).
F·G degrades as h → 0.

```python
def make_variable_apex(L: float, h: float) -> np.ndarray:
    r = L / np.sqrt(3)
    base_z = -h / 4
    return np.array([
        [0, 0, 3*h/4],
        [r, 0, base_z],
        [-r/2, r*np.sqrt(3)/2, base_z],
        [-r/2, -r*np.sqrt(3)/2, base_z],
    ])
```

---

## 5. KEY EXPERIMENTS

### Experiment 1: Bundle radius sweep
Sweep r_bundle from 0 to 0.1L with N=10.
Plot: ‖F·G‖ vs r_bundle/L (expect quadratic growth).

### Experiment 2: Solenoid spacing sweep
Sweep N_turns from 1 to 100 at r_coil = 0.03L.
Plot: ‖F·G‖ vs N_turns. Find the transition point.

### Experiment 3: Variable apex sweep
Sweep h from 0 to L√(2/3).
Plot: κ(F·M), ‖F·G‖, Laplacian eigenvalues.

### Experiment 4: Variable solenoid spacing
Use spacing_profile = lambda t: 1 + A*cos(2π*t).
Plot: centroid field quality vs spacing parameter A.

---

## 6. ANTI-PATTERNS

1. Do NOT implement racetrack coils. Never modeled correctly.
2. Do NOT put segment generators in k4_frozen.
3. Do NOT assume solenoids preserve F·G = 0.
4. Do NOT cite racetrack performance numbers from prior sessions.
5. Do NOT model bundle as "N × single wire" when r_bundle > 0.
6. biot_savart_segment lives in k4_frozen/field_engine.py — import it.

---

## 7. HARDWARE ROADMAP

Phase 1: L=500mm single wire, AH49E Hall sensors, Teensy.
Phase 2: Bundled wire (5-20 per edge) for field amplification.
Phase 3: Explore solenoid winding, measure F·G degradation.
Racetrack: stays in R&D notebook until correctly modeled.
