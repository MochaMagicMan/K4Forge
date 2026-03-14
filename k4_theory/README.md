# k4_theory — Independent Verification Oracle

Self-contained theorem mining, proof chain, and candidate discovery engine
for the K4 tetrahedral electromagnetic field control system.

**Does NOT import from k4_frozen.** This is intentional: k4_theory serves as
a parallel verification oracle that cross-checks results without sharing code
paths. Tests validate that the two agree.

## Quick start

```bash
# Run the full proof chain (46+ theorems)
python -m k4_theory --prove

# Run the S4 symmetry miner (discovers identities from permutation group)
python -m k4_theory --mine

# Run candidate discovery (generates and verifies new conjectures)
python -m k4_theory --discover

# All phases
python -m k4_theory
```

### Example: proof chain output

```
======================================================================
  K4 PROOF CHAIN -- Complete Verification
======================================================================

  L0_DEC_SPECTRAL
  ──────────────────────────────────────────────────────────────────
    T0.1       L0 = 4I4 - J4                 PROVED   (0.01 s)
    T0.2       CT*DT = 0                     PROVED   (0.00 s)
    T0.3       L1 = 4*I6                     PROVED   (0.00 s)
    ...
    INT.CG_zero  C_INT*G = 0 (integer)       PROVED   (0.02 s)
    INT.CM_eq_neg2S  C_INT*M = -2*S           PROVED   (0.01 s)

  L1_TOPOLOGY
  ──────────────────────────────────────────────────────────────────
    T1.1       MT*G = 0                       PROVED   (0.00 s)
    T1.7       P_cyc + P_cut = I6             PROVED   (0.00 s)
    ...

  ==================================================================
  47/47 proved, 0 failed
  ==================================================================
```

### Example: symmetry mining output

```
======================================================================
  S5: SYMMETRY MINING ENGINE -- 24 symmetries x 2 spaces
======================================================================

  FULL NULL: swap(0,1)     cut/invariant on axis    e=1.2e-15
  COMP NULL: (01)(23)      cycle/anti_inv on plane  e=3.4e-08
  ...

  Total discoveries: 28
    full_null on axis (cycle): 6
    component_null on plane (cut): 12
    ...
```

## Authoritative vs Exploratory

| Source | Role | Authority |
|--------|------|-----------|
| `k4_frozen/truth_kernel.py` | Immutable algebraic core | **Authoritative.** All other code imports from here. Never edited without version bump + full audit. |
| `k4_frozen/verify_all.py` | 182-check self-test | **Authoritative.** Regression gate. |
| `k4_theory/theory_miner.py` | Independent proof chain + discovery | **Exploratory.** Parallel verification oracle. May contain conjectures. Cross-validated against frozen in tests. |

**Rule:** If k4_theory and k4_frozen disagree, k4_frozen wins. The disagreement
itself is valuable — it means something needs investigation.

**Promotion path:** A theorem proven in k4_theory at tier T0 (integer-exact)
can be promoted to a `verify_layer1()` check in k4_frozen after independent
review and explicit version bump.

## Theorem inventory

### T0 — Integer Exact (DEC & Spectral)

| ID | Statement | What it proves |
|----|-----------|----------------|
| T0.1 | L0 = 4I - J | K4 vertex Laplacian spectral uniqueness |
| T0.2 | C^T D^T = 0 | DEC chain exactness |
| T0.3 | L1 = 4I6 | Edge Laplacian is scalar multiple of identity |
| T0.4 | D M = 0 | Boundary operator kills cycles |
| T0.6 | D C^T_T = 0 | Boundary of face = 0 |
| T0.7 | C^T D^T = 0 | Transpose DEC chain |
| T0.8 | D_red^T = G | Reduced incidence transpose equals cut basis |
| T0.12 | M^T (D^T D - 2I) G = 0 | Hodge-Sigma orthogonality |
| T0.14 | M^T A_opp G = rank-1 integer | Opposite-edge coupling structure |
| T0.15 | \|\|M^T A_opp G\|\|^2_F = 9 | Frobenius norm of opposite coupling |

### INT — Integer Field Structure

| ID | Statement | What it proves |
|----|-----------|----------------|
| INT.C | C_INT construction | Cross-product field matrix has entries in {-1,0,+1} |
| INT.CM_eq_neg2S | C_INT M = -2S | Field-cycle product is twice the sign matrix |
| INT.CG_zero | C_INT G = 0 | Cut annihilation to Integer(0) — no Biot-Savart needed |
| INT.det_CM_32 | det(C_INT M) = 32 | Controllability determinant is exact integer |
| INT.gram_CM | (C_INT M)^T(C_INT M) = 4 Gram | Controllability Gram, kappa=2 |
| INT.STS_gram | S^T S = Gram | Sign matrix squared is 4I-J |
| INT.isotropy | S adj S^T = 16I | Centroid isotropy via adjugate |
| INT.DELTA_M_zero | DELTA M = 0 | Edge direction signs annihilate cycles |
| INT.adj_check | Gram adj = 16I | Adjugate correctness |

### T1 — Algebraic Exact (Topology)

| ID | Statement | What it proves |
|----|-----------|----------------|
| T1.1 | M^T G = 0 | Hodge orthogonality (cycle perp cut) |
| T1.2 | D M = 0 | Kirchhoff compatibility |
| T1.3 | M^T M = G^T G = 4I-J | Gram identity |
| T1.4 | det(M^T M) = 16 | Gram determinant |
| T1.5 | det([M\|G]) = +/-16 | Full-space determinant |
| T1.6 | M+ G = G+ M = 0 | Pseudoinverse orthogonality |
| T1.7 | P_cyc + P_cut = I6 | Projector completeness |
| T1.8 | P_cyc P_cut = 0 | Projector orthogonality |

### T2 — Closed-form (Ring-quiet & Inductance)

| ID | Statement | What it proves |
|----|-----------|----------------|
| T2.1 | det(G_ring) = 0 | Ring solvability condition |
| T2.2 | null(G_ring) = span{1,1,1} | Ring null space is uniform |
| T2.3 | Ring-quiet iff J1+J2+J3=0 | Balanced cycle condition |
| T2.5 | M_opp = 0 | Opposite edges have zero mutual inductance (perpendicularity) |
| T2.6 | M^T L G = 0 | Hodge-inductance decoupling survives L matrix |
| T2.7 | L eigenvalue degeneracy | 3-fold degenerate cycle and cut eigenvalues |

### T3 — Parametric (Electromagnetics)

| ID | Statement | What it proves |
|----|-----------|----------------|
| T3.1 | F G = 0 | Cut annihilation at centroid (Biot-Savart) |
| T3.2 | det(F M) != 0 | Controllability determinant nonzero |
| T3.3 | rank(F M) = 3 | Full 3D B-field control |

### Sel — Selection Rules (Multipole)

| ID | Statement | What it proves |
|----|-----------|----------------|
| Sel.1 | Cut dipole = 0 | Cut currents produce zero dipole moment |
| Sel.2 | Cut quadrupole = 0 | Cut currents produce zero quadrupole moment |
| Sel.3 | Cycle octupole = 0 | Cycle currents produce zero octupole moment |

### SYM — Symbolic (Parametric in L)

| ID | Statement | What it proves |
|----|-----------|----------------|
| SYM.geom | Edge geometry exact | All edges=L, opposite edges perpendicular |
| SYM.F0G | F0 G = 0 | Cut annihilation via symbolic finite-wire Biot-Savart |
| SYM.F0M | det(F0 M), kappa=2 | Field matrix structure and condition number |
| SYM.sign | F0 M = alpha S | Field-cycle product factorizes as scalar times sign matrix |
| SYM.neumann | asinh(1/sqrt3) = ln(sqrt3) | Neumann integral sub-identity |
| SYM.null | Null tetrahedron | Face/edge nulls, rank structure |
| SYM.Evol | E_vol kappa = 2 | Barycentric gradient eigenvalues |

## Claim class mapping

| Tier | Claim class | Meaning |
|------|-------------|---------|
| T0, INT | **[A]** | Algebraic exact — integer identity, unconditional |
| T1 | **[A]** | Algebraic exact — graph topology, unconditional |
| T2 | **[G]** | Geometry-dependent exact — requires regular K4 |
| T3, SYM | **[G]** | Geometry-dependent — requires regular K4 + Biot-Savart |
| Sel | **[M]** | Numerical — verified to tolerance, not a proof |
| T4 (future) | **[M]** | Numerical — Monte Carlo or grid convergence |

## Import rules

```
k4_theory may import:    numpy, sympy, stdlib
k4_theory must NEVER import: k4_frozen, k4_explorer, k4_artifacts, k4_viz, k4_cli
```

This is enforced by `tests/test_theory_miner.py::test_theory_miner_is_self_contained`,
which walks the AST of every `.py` file in k4_theory/.
