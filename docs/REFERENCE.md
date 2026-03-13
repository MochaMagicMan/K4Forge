# K4 TETRAHEDRAL ELECTROMAGNETIC FRAMEWORK
## Frozen Reference v3.0.0

**Frozen from:** v1.2.0 + Sessions through 2026-03-07
**Accompanies:** `k4_frozen_v3/` Python package (v3.0.0)
**Consistency check:** `python -m k4_frozen_v3.verify_all` (176 tests, internal consistency only)
**This document IS the continuation.** A new chat with this package can resume work.

---

## What This System Is

A regular tetrahedron with 6 edge conductors and 4 vertex electrodes.
The 6 edge currents form I in R^6 which splits exactly into cycle space
(3D, closed loops, satisfies KCL) and cut space (3D, discrete gradients,
requires vertex injection via supply rail). At the centroid, cycle currents
produce B-field with full 3D control; cut currents produce exactly zero
B-field. Vertex electrodes independently produce E-field.

Result: 9 DOF (3 cycle + 3 cut + 3 voltage), 6 independent field outputs
(Bx, By, Bz, Ex, Ey, Ez) at centroid, 3 remaining DOF for spatial shaping.

---

## Why a Tetrahedron

K4 is the unique complete graph whose Laplacian eigenvalue lambda=n (here n=4)
has multiplicity exactly 3. Spectrum of K4: {0, 4, 4, 4}.
K4 is the only Kn where dim(cycle) = dim(cut) = 3.
Edge Laplacian L1 = 4*I6 -- scalar -- all edges identical topologically.

---

## Layer Architecture

```
LAYER 0:   Integer Matrices             --- UNCONDITIONAL
LAYER 1:   Graph Theory                 --- GEOMETRY-INDEPENDENT
LAYER 1.7: Sign Matrix S, Gram inv     
LAYER 3-4: Electromagnetics             --- MODEL: Biot-Savart + centroid
LAYER 4W:  Full-Wave Impedance          --- MODEL: retarded kernel (magnetoquasistatic)
LAYER S4:  Commutant / Rep Theory       --- [A]+[G]: ζ₄=1/7, 2-design
LAYER 5:   Bose-Mesner Algebra          
LAYER 6:   Spherical Harmonics          
LAYER 7:   Sphere Sculpting             
CONTROL:   Ring-Quiet Mode              --- [A]: algebraic cancellation
```

Layers 0-1.7 are immutable. Layers 3+ depend on the model.

---

## Frozen Matrices

```
M (cycle basis, 6x3):          G (cut basis, 6x3):
E01: [-1,  0,  1]              E01: [ 1,  0,  0]
E02: [ 1, -1,  0]              E02: [ 0,  1,  0]
E03: [ 0,  1, -1]              E03: [ 0,  0,  1]
E12: [-1,  0,  0]              E12: [-1,  1,  0]
E13: [ 0,  0,  1]              E13: [-1,  0,  1]
E23: [ 0, -1,  0]              E23: [ 0, -1,  1]

D (incidence, 4x6):
     E01 E02 E03 E12 E13 E23
V0: [-1, -1, -1,  0,  0,  0]
V1: [ 1,  0,  0, -1, -1,  0]
V2: [ 0,  1,  0,  1,  0, -1]
V3: [ 0,  0,  1,  0,  1,  1]

S (sign matrix, 3x3):
    [-1, +1, -1]
    [-1, -1, +1]
    [+1, -1, -1]

Vertices: V0=(1,1,1) V1=(1,-1,-1) V2=(-1,1,-1) V3=(-1,-1,1)
Edge length: L = 2*sqrt(2).  Vertex-centroid: sqrt(3).  Midpoint-centroid: 1.0.
```

---

## The Gram and Its Inverse

```
Gram = M^T*M = G^T*G = 4*I3 - J3    (diag=3, off=-1)
det(Gram) = 16
Eigenvalues: {1, 4, 4}   (breathing, differential x2)
```

Gram^{-1} = (1/4)*I + (1/4)*J (diag=1/2, off=1/4)

In (alpha,beta) notation: alpha=1/4, beta=1/4.
Verification: (4,-1)*(1/4,1/4) = (1, 1-1/4-3/4) = (1,0) = I.

DRIFT LOG: v1 had Gram^{-1} = (1/3)*I + (1/9)*J. WRONG. Caught by Gram*Gram^{-1} != I.

---

## The Sign Matrix S

At centroid: F0*M = c * S where c ~ 2.309e-7 for unit coordinates.

S encodes everything:
- S^T*S = 4I-J = Gram (S is "square root" of Gram)
- S*Gram^{-1}*S^T = I3 (centroid isotropy, kappa_intrinsic = 1)
- S eigenvalues: -1 (breathing), -1 +/- i*sqrt(3) (rotation, |lambda|=2)
- Eigenvector for -1: [1,1,1] (breathing mode)
- Eigenvector for -1-i*sqrt(3): (1,omega,omega^2) where omega=exp(-2*pi*i/3)
- C_INT @ M = -2*S (integer identity)

---

## Bose-Mesner Algebra {alpha*I + beta*J} (Layer 5)

On C3 symmetry axes, ALL cycle-space operators commute with S3 and live in
span{I3, J3}. Every operator = alpha*I + beta*J.

Symmetry: Axis-adapted commutant is with respect to the C3 stabilizer
(S3 action on the 3 remaining vertices); full S4-equivariance on the
6-edge space is a separate, stronger check.

Multiplication: (a1,b1)*(a2,b2) = (a1*a2, a1*b2+b1*a2+3*b1*b2)
Eigenvalues: lambda_br = alpha+3*beta, lambda_diff = alpha
Condition number: R = 1+3*beta/alpha, kappa = sqrt(max(R,1/R))

```
Operator      alpha   beta    lambda_br  lambda_diff   kappa
I             1       0       1          1             1
J             0       1       3          0             inf
Gram          4      -1       1          4             2
Gram^{-1}     1/4     1/4     1          1/4           2
Gram^2        16     -5       1          16            4
P_par=J/3     0       1/3     1          0             inf
P_perp=I-J/3  1      -1/3     0          1             inf
```

KEY: lambda_br = 1 for ALL powers of Gram. Breathing is conserved.

beta/alpha along C3: NO closed form. Pade KILLED (92% error at t=0.5).
Endpoints: t=0 -> beta=0, kappa=1; t->vertex -> beta/alpha->-1/3, kappa->inf.

SCOPE: Exact for symmetry-equivariant operators on C3 axes of the regular
tetrahedron. Elsewhere, (alpha,beta) are a best-fit projection and epsilon
is the honesty meter measuring departure from the algebra.

---

## Spherical Harmonics (Layer 6)

K4 with 3 cycle DOF = complete l=1 spherical harmonic synthesizer:

- m=0 (breathing): DC drive [1,1,1] -> axial B along [1,1,1]
- m=+/-1 (rotation): 3-phase -> circular B perpendicular to [1,1,1]
- Perfect circle (std/mean < 1e-16)
- Breathing and rotation DECOUPLED at centroid

Response on input sphere: |S*w|^2 = 4 - (sum(w_i))^2
Content: l=0 (avg=3) + l=2. No l>=3 (Clebsch-Gordan: 1 x 1 = 0+1+2).

---

## Sphere Sculpting (Layer 7)

NULL RESULT: AM 3-phase cannot sculpt. Must break the orbit.

Sculpting = breaking S3 symmetry. Energy-normalized at R=0.3:

```
Waveform              Contrast   Mechanism
Pulsed toward target  0.647      Duty-cycle concentration
Elliptical orbit      0.541      Stretched footprint
DC bias               0.300      Displaced rotation center
Uniform 3-phase       0.420      Geometric baseline (NOT uniform!)
```

Energy split: 33.1% radial (push), 66.9% tangential (sweep). Universal.

---

## Proven Theorems

### Layer 0-1 Algebraic [A] (Integer(0)):
T1.1 M^T*G=0 | T1.2 D*M=0 | T1.3 Gram=4I-J | T1.4 det=16 | T1.5 |det[M|G]|=16
T1.7 P_C+P_G=I6 | T1.8 P_C*P_G=0 | L1=4I6 | D*B=0 | P5 D_red^T=G

### Sign matrix identities [A]: S^T*S=Gram | C_INT@M=-2S | S*Gram^{-1}*S^T=I3

### Layer 3-4 Geometric [G]:
T3.1 F0*G=0 | T3.2 det(F0M)!=0 | T3.3 rank(F0M)=3

### Extended results [G]/[M]:
T4.1 3-phase circular | T4.2 Breathing/rotation decoupled
T4.3 |S*w|^2=4-sum(w)^2 | T4.4 S4 spectral equiv | T4.5 AM null

---

## 10 Verified Isomorphisms

```
ISO1  F0*M = c*S                          PROVED
ISO2  S^T*S = Gram = 4I-J                 PROVED
ISO3  S*Gram^{-1}*S^T = I3               PROVED
ISO4  Cycle-field op in {aI+bJ} on C3    PROVED
ISO5  All C3 axes equivalent              PROVED (axis-adapted extraction required)
ISO6  Magic angle = arccos(1/sqrt(3))     PROVED
ISO7  F0*G = 0                            PROVED
ISO8  Inductance in span{I, D^T*D}       VERIFIED
ISO9  E = -G for linear potential          PROVED
ISO10 L1 = 4*I6                           PROVED
```

---

## Dark Lines

7 lines through centroid: 4 C3 axes + 3 C2 axes.
Bouquet topology. Incidence = Steiner triple system, NOT Fano (refuted).
Magic angle C3<->C2: arccos(1/sqrt(3)) = 54.7356 deg = NMR magic angle.

---

## Corrections That Must Not Regress

1. Gram^{-1} = (1/4,1/4) not (1/3,1/9). Always verify Gram*X=I.
2. No Pade for beta/alpha. Compute numerically.
3. AM 3-phase = null result. Direction must change, not just amplitude.
4. kappa_intrinsic=1 at centroid. kappa=2 is basis Gram condition.
5. Axis-adapted commutant is S3 (C3 stabilizer), not full S4.
6. Not a Fano plane. Steiner triple system.
7. Conductors are conductors. E/B separation is Config D design, not physics.
8. Cut/cycle are pattern descriptors, not hardware modes.
9. Centroid is symmetry fixed point, not universally "best."

---

## What Breaks When (Diagnostic Probes)

```
Change               Breaks Tier  Observable Symptom                  Gate That Trips
─────────────────    ───────────  ──────────────────────────────────  ──────────────────────
Irregular tetra      Layer 3+     F0·G ≠ 0, kappa ≠ 2, ε grows      T3.1, P13, BM5
Off-centroid eval    Layer 4+     Cut not annihilated, F·G ≠ 0       T3.1 (at centroid only)
Thick wire / bundles Layer 4+     Biot-Savart residual grows          verify_layer4 scale_inv
Higher frequency     Layer 4+     Inductance L·dI/dt term dominates  regime_analysis
Off C3 axis          Layer 5      ε > 0 in Bose-Mesner extraction    BM5 (ε honesty meter)
Coupled E/B          Hardware     Config D independence lost          enforce_config_contract
Non-DC regime        Hardware     Skin depth, radiation corrections   preflight regime check
Multi-cell array     Extension    Inter-cell coupling unmodeled       EXTENSION_CHECKLIST
```

Integer identities (Layer 0-1) survive ALL of the above — they are unconditional.

---

## Hardware Configurations

```
Config  Structure                    B DOF  E DOF  Best for
A       6 independent coils         6      0      Simple B-only
B       Connected network           3      0      Constrained
C       Connected + vertex sources  6      3      Full but coupled
D       Separate coils + electrodes 6      3      Best E/B independence
E       Connected + electrodes      6      3      Full + coupled
```

---

## Control Formulas

Centroid inversion (exact):
```
w1 = -sqrt(6)*L*(Bx+By)/32
w2 = -sqrt(6)*L*(By+Bz)/32
w3 = -sqrt(6)*L*(Bx+Bz)/32
I = M*w + G*u    (u free at centroid)
```

Off-centroid kappa along C3:
```
t=0.0: 1.000   t=0.3: 1.842   t=0.7: 4.315
t=0.1: 1.224   t=0.5: 2.796   t=0.9: 6.847
```

---

## Open Frontiers (top 5 of 28)

1. delta1: AC null structure -- at what frequency does cut->B leakage begin?
2. gamma1: Planar tetrahedron (h->0) -- path to PCB arrays
3. alpha2: L1=4I6 consequences -- edge democracy, fault tolerance
4. beta3: Self-duality <-> E/B independence -- uniqueness theorem?
5. zeta4: 1/7 mystery -- ||dF/dx*G||/||dF/dx*M|| ~ 1/7. No proof.

---

## File Map

```
truth_kernel.py          Layer 0-1.7   M,G,D,S,Gram inv + proofs
field_engine.py          Layer 3-4     Biot-Savart, F matrix, centroid inversion
symbolic_proofs.py       Layer 3-4     SymPy exact EM proofs (F₀·G=0, det, eigenvalues)
full_wave.py             Layer 4W      Retarded kernel Z(ω), Hodge-impedance decoupling
commutant.py             Layer S4      S₄ rep theory, ζ₄=1/7, Σ eigenvalues, 2-design
ring_quiet.py            Control       Algebraic ring-edge cancellation
bose_mesner.py           Layer 5       {αI+βJ} algebra, spectral κ
spherical_harmonics.py   Layer 6       3-phase, mode decompose
sphere_sculpt.py         Layer 7       Energy-normalized sculpt
null_tetrahedron.py      ---           Dark lines, null surfaces
inductance.py            Layer 4+      Neumann integrals, Hodge-L decoupling, control
session_schema.py        ---           Result tagging
session_compiler.py      ---           Solver + regression (12 canonical sessions)
policy.py                ---           Claim enforcement, config gates
assumptions.py           ---           Physics regime declarations, preflight
integration.py           ---           Non-ideal geometry docking, multi-cell
diagnostics.py           ---           Spectral diagnostics (manual inspection)
verify_all.py            ALL           176 consistency checks, 15 sections
REFERENCE.md             ---           This document (the handoff)
RECIPES.md               ---           Integration patterns, worked examples
```

---

## Session Arc

Phase 1-3: Hypertoroid compiler, geometry audit, GPT drift analysis
Phase 4: Frozen stack v1 (68/68 tests)
Phase 5: Physics pivot -- inductance tensor, Hodge-inductance decoupling
Phase 6: Symbolic promotion cascade -- 26 claims promoted
Phase 7: S matrix discovery -- dipole structure, sqrt(Gram), centroid map
Phase 8: Null topology -- 7 dark lines, kappa=1, magic angle
Phase 9: Bose-Mesner algebra -- 2D commutant, S3 correction, Fano refuted
Phase 10: 10 isomorphisms, Gram inv corrected, Pade killed
Phase 11: Cockpit + 28-seed pod
Phase 12: Spherical harmonics -- l=1 synthesizer, decoupling
Phase 13: Sphere sculpting -- null result, S3 symmetry breaking
Phase 14 (v3.0): Centroid inversion corrected (direct solve)
Phase 15 (v3.0): Full-wave extension -- Z(ω), Hodge-impedance decoupling
Phase 16 (v3.0): S₄ commutant -- ζ₄=1/7 proof, gradient complementarity
Phase 17 (v3.0): Ring-quiet mode formalization
Phase 18 (v3.0): Regime limitations documented, ε gate tightened, 176 tests

---

## How to Resume

```python
python -m k4_frozen_v3.verify_all    # confirm consistency

from k4_frozen_v3 import M, G, D, S, make_vertices, field_at_centroid
from k4_frozen_v3 import centroid_inversion, e_field_volume_matrix
from k4_frozen_v3 import compute_zeta4, verify_commutant, irrep_atlas
from k4_frozen_v3 import compute_ring_quiet, canonical_vortex_mode
from k4_frozen_v3 import verify_full_wave, radiation_asymmetry
from k4_frozen_v3 import ab_kappa, spectral_coordinates
from k4_frozen_v3 import command_dc, command_ac, command_rotating
```

Opening message: "Working from k4_frozen_v3 v3.0.0. verify_all passes
(176 internal consistency checks). Centroid inversion uses direct solve.
Ready for [next priority]."

---

*End of K4 Frozen Reference v3.0.0*
