# CANONICAL VIEWPORT & FIGURE SPEC
## For Claude Code: implement this, not guesses

---

## BUG IN CURRENT observables.py

Line 38: `v0_dir = c - V[0]` points FROM V0 TOWARD centroid.
This means VP-04 and VP-05 are placed AWAY from V0 (toward opposite face),
which is WRONG. The Doctrine says "vertex axis 0.3L" means 0.3L from
centroid TOWARD V0.

Fix: `v0_dir = V[0] - c` (from centroid toward V0).

For regular tetrahedron with centroid at origin: V[0] - c = V[0],
so v0_hat = V[0] / |V[0]|.

---

## CANONICAL VIEWPORT POSITIONS (from Doctrine §4 + Viewport Atlas)

Each viewport has a structural role. Positions are defined relative to
the geometry, not hardcoded Cartesian coordinates.

| VP | Name | Position | Direction | Role | Claim |
|----|------|----------|-----------|------|-------|
| VP-01 | Centroid | centroid (origin for regular) | — | Theorem witness: F·G=0, rank(FM)=3 | [G] |
| VP-02 | Shell | centroid + 0.05L toward V0 | C3(V0) | Gradient / local robustness | [M] |
| VP-03 | Face center | (V1+V2+V3)/3 (face opposite V0) | — | Interior texture, cut emergence | [M] |
| VP-04 | Vertex axis near | centroid + 0.3L toward V0 | C3(V0) | Cut emergence (34% of cycle) | [M] |
| VP-05 | Vertex axis far | centroid + 0.6L toward V0 | C3(V0) | Extreme field, κ=782:1 | [M] |
| VP-06 | Edge midpoint | (V0+V1)/2 | — | Singular-structure probe | [M] |
| VP-07 | Exterior 1L | centroid + 1.0L toward V0 | C3(V0) | Crossover witness (cut=3.5× cycle) | [M] |
| VP-08 | Exterior 3L | centroid + 3.0L toward V0 | C3(V0) | Monopole territory (cut=8× cycle) | [M] |
| VP-09 | Null ring | centroid + 0.1L in x-direction | arbitrary | Null orbit benchmark | [M] |

IMPORTANT: VP-02 through VP-08 (except VP-03 and VP-06) all use the SAME
C3 axis (toward V0) so their results are directly comparable along one
radial line. VP-09 is deliberately OFF the C3 axis to test non-symmetric behavior.

### Corrected code for _viewport_positions:

```python
def _viewport_positions(ctx: FieldContext) -> dict:
    V = ctx.V
    L = ctx.L
    c = V.mean(axis=0)  # centroid

    # C3 axis: centroid toward V0
    v0_dir = V[0] - c
    v0_hat = v0_dir / np.linalg.norm(v0_dir)

    # Face center opposite V0
    face_center_0 = (V[1] + V[2] + V[3]) / 3

    # Edge midpoint E01
    edge_mid_01 = (V[0] + V[1]) / 2

    return {
        "VP-01": c,                                    # Centroid
        "VP-02": c + 0.05 * L * v0_hat,               # Shell 0.05L
        "VP-03": face_center_0,                        # Face center F0
        "VP-04": c + 0.3 * L * v0_hat,                # Vertex axis 0.3L
        "VP-05": c + 0.6 * L * v0_hat,                # Vertex axis 0.6L
        "VP-06": edge_mid_01,                          # Edge midpoint E01
        "VP-07": c + 1.0 * L * v0_hat,                # Exterior 1L (same axis)
        "VP-08": c + 3.0 * L * v0_hat,                # Exterior 3L (same axis)
        "VP-09": c + 0.1 * L * np.array([1, 0, 0]),   # Null ring (off-axis)
    }
```

---

## FIGURE SPECIFICATIONS

### Figure 1: geometry.png — 3D Tetrahedron

What to show:
- 4 vertices as labeled scatter points (V0, V1, V2, V3)
- 6 edges as wireframe lines (E01–E23)
- Centroid as star marker
- 4 face centers as small dots
- 9 viewport positions as colored markers with VP-XX labels
- Edge lengths annotated

Stamp: `[G] Regular K4, L = {L*100:.1f} cm`

Camera angle: azim=-60, elev=25 (standard perspective, NOT the
flat-square trap where all 4 corners look like a square)

Color scheme: vertices in red, edges in black, centroid gold star,
face centers gray, viewport markers by family:
  - VP-01: gold (centroid)
  - VP-02,03: blue (certification panel)
  - VP-04,07,08: green (cut characterization panel)
  - VP-05,06: orange (stress panel)
  - VP-09: purple (null orbit panel)

### Figure 2: field_slice.png — B-field in z=0 Plane

What to show:
- 2D pcolormesh of |B| on a grid in the z=0 plane
- Quiver arrows showing B direction (Bx, By components)
- Vertex positions projected onto z=0 as markers
- Edge lines projected onto z=0
- Centroid marker
- Colorbar with units (µT)

Grid: 25×25 spanning [-2L, 2L] in x and y
Field computation: B(r) = F(r) · I_edge for each grid point
Color scale: log or linear depending on dynamic range

Stamp: `[M] Biot-Savart, z=0 slice, I from basic-bz`

### Figure 3: probe_summary.png — 9-Viewport Bar Chart

What to show:
- Horizontal bar chart with 9 bars (one per viewport)
- Bar length = |B| at that viewport (µT scale)
- Bar color by claim class: gold=[G], blue=[M]
- Text annotation on each bar: B components, selectivity
- Panel grouping (Panel 1: VP-01,02,03 | Panel 2: VP-04,07,08 | etc.)

Columns for each viewport:
  VP-ID | |B| bar | Bx,By,Bz | Selectivity | Claim

Stamp: per-viewport claim class in the label

---

## PANEL STRUCTURE (from Canonical Panels spec)

For future implementation, the 4 panels map to viewports as:

Panel 1 CERTIFICATION: VP-01, VP-02, VP-03
  "Is the field program correct?"

Panel 2 CUT CHARACTERIZATION: VP-04, VP-07, VP-08
  "What is the cut-coil channel doing?"
  Key metric: selectivity ratio at each viewport + crossover profile

Panel 3 STRESS: VP-05, VP-06
  "Where is the system strained?"
  Key: locked color scale, current utilization bars

Panel 4 NULL ORBIT: VP-09, VP-01, VP-03 (conditional — only when null active)
  "How is the null behaving?"
  Key: effort polar plot for trajectory mode

---

## VIEWPORT EXPECTED VALUES (regression anchors for BASIC-BZ)

For B=[0,0,10µT], E=[100,0,0], DC, L=0.1m, regular K4:

| VP | Expected behavior |
|----|-------------------|
| VP-01 | |B|=10µT exact, selectivity=∞ (no cut drive), B_cut=0 |
| VP-02 | |B| slightly different from 10µT, selectivity still very high |
| VP-03 | |B| noticeably different, selectivity high but finite |
| VP-04 | |B| increasing (closer to vertex → stronger), selectivity decreasing |
| VP-05 | |B| much larger (near vertex), selectivity low, high κ |
| VP-06 | |B| very large (near edge), model may be unreliable |
| VP-07 | |B| small (exterior), selectivity would be inverted IF cut active |
| VP-08 | |B| very small (far exterior) |
| VP-09 | |B| near centroid value (only 0.1L away) |

Note: with u_coil=0 (BASIC-BZ has no cut drive), B_cut=0 everywhere,
so selectivity=∞ at all viewports. The selectivity structure becomes
visible with presets like NULL-ORBIT or CUT-REACH that activate u_coil.
