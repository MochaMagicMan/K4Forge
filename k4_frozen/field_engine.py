"""
field_engine.py — Layer 3–4: Geometry, Biot-Savart, & EM Theorems
=================================================================

MODEL-DEPENDENT. These results require:
  - Regular tetrahedron (Layer 3)
  - Biot-Savart thin-wire model (Layer 4)
  - Specific evaluation points

Claim classes: [G] geometric exact, [M] model-dependent numerical

Frozen at: K4 Definitive Reference v1.2.0
"""

import numpy as np
from typing import Tuple, Dict, Optional, List
from . import truth_kernel as tk

# ═══════════════════════════════════════════════════════════════════
# LAYER 3: GEOMETRIC CONSTANTS
# ═══════════════════════════════════════════════════════════════════

MU0 = 4.0e-7 * np.pi  # vacuum permeability (H/m)
DEFAULT_L = 0.1        # default edge length (m)


def make_vertices(L: float = DEFAULT_L) -> np.ndarray:
    """
    Regular tetrahedron vertices, centroid at origin.

    V₀ = s·[+1,+1,+1], V₁ = s·[+1,−1,−1],
    V₂ = s·[−1,+1,−1], V₃ = s·[−1,−1,+1]
    where s = L/(2√2), giving edge length = L exactly.

    Returns: (4,3) array of vertex coordinates.
    Claim: [G] (regular tetrahedron embedding)
    """
    s = L / (2.0 * np.sqrt(2.0))
    return np.array([
        [+s, +s, +s],   # V0
        [+s, -s, -s],   # V1
        [-s, +s, -s],   # V2
        [-s, -s, +s],   # V3
    ])


def make_edges(V: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Return list of (start, end) pairs for all 6 edges in canonical order."""
    pairs = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    return [(V[i], V[j]) for i, j in pairs]


def centroid(V: np.ndarray) -> np.ndarray:
    """Centroid of the tetrahedron (should be origin for canonical vertices)."""
    return V.mean(axis=0)


def face_centers(V: np.ndarray) -> np.ndarray:
    """
    Face centers. F_i is the face OPPOSITE vertex V_i.
    Returns (4,3) array.
    """
    fc = np.zeros((4, 3))
    for i in range(4):
        others = [j for j in range(4) if j != i]
        fc[i] = V[others].mean(axis=0)
    return fc


def edge_midpoints(V: np.ndarray) -> np.ndarray:
    """Edge midpoints in canonical order. Returns (6,3) array."""
    pairs = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    return np.array([(V[i] + V[j]) / 2.0 for i, j in pairs])


# ═══════════════════════════════════════════════════════════════════
# BIOT-SAVART FIELD COMPUTATION (finite segment, exact formula)
# ═══════════════════════════════════════════════════════════════════

def biot_savart_segment(P1: np.ndarray, P2: np.ndarray, r: np.ndarray,
                        I: float = 1.0, wire_radius: float = 0.0) -> np.ndarray:
    """
    Magnetic field at point r from a straight wire segment P1→P2
    carrying current I, using the exact finite-segment Biot-Savart formula.

    B = (μ₀I/4π) · (dl × r̂) / |r|² integrated analytically.

    If wire_radius > 0, the perpendicular distance is floored at
    wire_radius to prevent near-wire singularities. Inside a physical
    wire, B grows linearly with r (not 1/r), so capping the distance
    gives a physically reasonable upper bound.

    Returns B vector in Tesla.
    Claim: [G] (exact within thin-wire Biot-Savart model)
    """
    dl = P2 - P1          # wire direction
    r1 = r - P1           # vector from P1 to observation
    r2 = r - P2           # vector from P2 to observation
    dl_cross_r1 = np.cross(dl, r1)
    norm_cross = np.linalg.norm(dl_cross_r1)

    if norm_cross < 1e-30:
        return np.zeros(3)  # on the wire axis

    dl_hat = dl / np.linalg.norm(dl)
    r1_hat = r1 / np.linalg.norm(r1)
    r2_hat = r2 / np.linalg.norm(r2)

    # Perpendicular distance from wire axis
    perp_dist_sq = norm_cross**2 / np.dot(dl, dl)
    
    # Wire-radius floor: prevent 1/r singularity for near-wire probes
    if wire_radius > 0 and perp_dist_sq < wire_radius**2:
        perp_dist_sq = wire_radius**2

    factor = MU0 * I / (4.0 * np.pi)
    cos1 = np.dot(dl_hat, r1_hat)
    cos2 = np.dot(dl_hat, r2_hat)

    direction = dl_cross_r1 / norm_cross
    magnitude = factor * (cos1 - cos2) / np.sqrt(perp_dist_sq)

    return magnitude * direction


def field_matrix(r: np.ndarray, V: np.ndarray) -> np.ndarray:
    """
    Compute the 3×6 field matrix F(r) such that B(r) = F(r)·I.
    Column k is the B-field at r from unit current in edge k.

    Claim: [G] (regular tetrahedron + Biot-Savart + specific point)
    """
    edges = make_edges(V)
    F = np.zeros((3, 6))
    for k, (P1, P2) in enumerate(edges):
        F[:, k] = biot_savart_segment(P1, P2, r, I=1.0)
    return F


def field_at_centroid(V: np.ndarray) -> np.ndarray:
    """Compute F₀ = F(centroid). Returns 3×6 matrix."""
    c = centroid(V)
    return field_matrix(c, V)


# ═══════════════════════════════════════════════════════════════════
# LAYER 4: ELECTROMAGNETIC THEOREMS
# ═══════════════════════════════════════════════════════════════════

def verify_layer4(L: float = DEFAULT_L, verbose: bool = True) -> Dict[str, bool]:
    """
    Verify Layer 4 theorems:
      T3.1: F₀·G = 0 (cut annihilation at centroid)
      T3.2: det(F₀·M) ≠ 0 (cycle spanning)
      T3.3: rank(F₀·M) = 3
      P10/P11: σ₃/σ₁ = 1/2, σ₁ = σ₂ (2:1 anisotropy)
      P13: κ(F₀·M) = 2 (universal centroid anisotropy)

    Returns dict of {test_name: passed}.
    Claim: [G] (regular tetrahedron + Biot-Savart)
    """
    V = make_vertices(L)
    F0 = field_at_centroid(V)
    M_f = tk.M.astype(float)
    G_f = tk.G.astype(float)
    D_f = tk.D.astype(float)

    results = {}

    # T3.1: F₀·G = 0₃ₓ₃ (cut annihilation)
    F0G = F0 @ G_f
    norm_F0G = np.linalg.norm(F0G)
    results["T3.1_F0G_zero"] = (norm_F0G < 1e-14)

    # T3.2: det(F₀·M) ≠ 0
    F0M = F0 @ M_f
    det_F0M = np.linalg.det(F0M)
    results["T3.2_det_F0M_nonzero"] = (abs(det_F0M) > 1e-30)

    # T3.3: rank(F₀·M) = 3
    rank_F0M = np.linalg.matrix_rank(F0M)
    results["T3.3_rank_F0M_3"] = (rank_F0M == 3)

    # P10/P11: Singular values → 2:1 anisotropy
    svs = np.linalg.svd(F0M, compute_uv=False)
    svs_sorted = np.sort(svs)[::-1]  # descending
    ratio = svs_sorted[2] / svs_sorted[0]  # σ₃/σ₁
    results["P10_anisotropy_half"] = abs(ratio - 0.5) < 1e-10
    results["P11_degenerate_pair"] = abs(svs_sorted[0] - svs_sorted[1]) < 1e-10

    # P13: κ = σ₁/σ₃ = 2
    kappa = svs_sorted[0] / svs_sorted[2]
    results["P13_kappa_2"] = abs(kappa - 2.0) < 1e-10

    # Structural: D·M·w gives zero vertex injection for any w
    # (Already T1.2 but verify through F)
    results["structural_DM_zero"] = (np.linalg.norm(D_f @ M_f) < 1e-14)

    # Scale invariance: F₀·G = 0 for different L
    for L_test in [0.05, 0.2, 1.0]:
        V_test = make_vertices(L_test)
        F_test = field_at_centroid(V_test)
        norm_test = np.linalg.norm(F_test @ G_f)
        results[f"scale_inv_L{L_test}"] = (norm_test < 1e-14)

    # CENTROID INVERSION ROUNDTRIP (trust surface safeguard)
    # This was wrong in prior versions — extra vigilance warranted.
    # Test 6 independent directions to catch any constant/scaling bug.
    test_targets = [
        np.array([1e-5, 0, 0]),       # pure x
        np.array([0, 1e-5, 0]),       # pure y
        np.array([0, 0, 1e-5]),       # pure z
        np.array([3e-6, 4e-6, 5e-6]),  # arbitrary
        np.array([-7e-6, 2e-6, 1e-6]), # negative component
        np.array([1e-6, 1e-6, 1e-6]),  # along (1,1,1) — the hard axis
    ]
    for idx, B_tgt in enumerate(test_targets):
        w_test = centroid_inversion(B_tgt, L)
        B_ach = F0 @ (M_f @ w_test)
        err = np.linalg.norm(B_ach - B_tgt)
        results[f"inversion_roundtrip_{idx}"] = (err < 1e-15)

    if verbose:
        print("=" * 60)
        print(f"LAYER 4 VERIFICATION (L = {L} m)")
        print("=" * 60)
        print(f"  ‖F₀·G‖ = {norm_F0G:.2e}")
        print(f"  det(F₀·M) = {det_F0M:.6e}")
        print(f"  σ₁, σ₂, σ₃ = {svs_sorted[0]:.6f}, {svs_sorted[1]:.6f}, {svs_sorted[2]:.6f}")
        print(f"  κ(F₀M) = {kappa:.6f}")
        print(f"  σ₃/σ₁ = {ratio:.6f}")
        print()
        all_pass = True
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")
            if not passed:
                all_pass = False
        n = len(results)
        p = sum(results.values())
        print(f"\n  {p}/{n} tests passed")

    return results


# ═══════════════════════════════════════════════════════════════════
# E-FIELD MODEL (Level 2: Barycentric/Laplace surrogate)
# ═══════════════════════════════════════════════════════════════════

def e_field_volume_matrix(V: np.ndarray) -> np.ndarray:
    """
    Compute E_vol (3×3): E = -E_vol · u
    where u = [V₁, V₂, V₃] (V₀=0 gauge).

    Uses barycentric coordinate gradients of the regular tetrahedron.

    MODEL ASSUMPTIONS:
      - E-field is UNIFORM throughout the interior (exact for Laplace
        equation with linear boundary conditions on a simplex).
      - Electrodes are POINT sources at vertices (no finite electrode
        size correction).
      - The model does NOT compute E-field outside the tetrahedron or
        near edges where conductor geometry matters.
      - AC E-fields (capacitive coupling, displacement current) are
        NOT modeled — this is an electrostatic approximation.
      - Off-centroid E-field equals centroid E-field (uniform interior
        is the model, not an approximation within the model).

    Claim: [G] (exact for regular tetrahedron barycentric model)
    """
    # Barycentric coordinate gradients: ∇λ_i = n_i / (3·V_tet)
    # where n_i is inward face normal of face opposite V_i, scaled by face area
    # For regular tet with V₀ as reference:
    # E = -∇V = -(V₁·∇λ₁ + V₂·∇λ₂ + V₃·∇λ₃)

    L = np.linalg.norm(V[0] - V[1])
    # Volume of regular tetrahedron
    vol = L**3 / (6.0 * np.sqrt(2.0))

    # Face normals (inward, face i opposite vertex i)
    E_vol = np.zeros((3, 3))
    for i in range(1, 4):  # V₁, V₂, V₃ (V₀ is reference)
        # ∇λ_i points from face_i toward vertex_i
        face_center = face_centers(V)[i]
        grad_lambda_i = (V[i] - face_center)
        # Normalize: ∇λ_i · (V_i - face_center_i) = 1
        grad_lambda_i = grad_lambda_i / np.dot(grad_lambda_i, V[i] - face_center)
        E_vol[:, i-1] = grad_lambda_i

    return E_vol


def verify_e_field(L: float = DEFAULT_L, verbose: bool = True) -> Dict[str, bool]:
    """Verify E-field model properties."""
    V = make_vertices(L)
    Ev = e_field_volume_matrix(V)
    results = {}

    results["E_vol_rank_3"] = (np.linalg.matrix_rank(Ev) == 3)
    kappa_E = np.linalg.cond(Ev)
    results["E_vol_kappa_2"] = abs(kappa_E - 2.0) < 0.1  # P13 applies here too

    if verbose:
        print("=" * 60)
        print(f"E-FIELD VERIFICATION (L = {L} m)")
        print("=" * 60)
        print(f"  rank(E_vol) = {np.linalg.matrix_rank(Ev)}")
        print(f"  κ(E_vol) = {kappa_E:.4f}")
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")

    return results


# ═══════════════════════════════════════════════════════════════════
# CENTROID INVERSION (exact symbolic formula)
# ═══════════════════════════════════════════════════════════════════

def centroid_inversion(B_target: np.ndarray, L: float = DEFAULT_L) -> np.ndarray:
    """
    Compute cycle weights w such that F₀·M·w = B_target at centroid.

    Uses direct numerical solve of the 3×3 system (F₀·M)·w = B.
    This is exact for the regular tetrahedron (det(F₀·M) ≠ 0 by T3.2).

    The structural form is:
        w₁ = −(Bx + By)/(2k)
        w₂ = −(By + Bz)/(2k)
        w₃ = −(Bx + Bz)/(2k)
    where k = 2μ₀√6/(3πL).  For L=0.1m: k ≈ 6.53×10⁻⁶ T/A.

    NOTE: Prior versions used an incorrect closed-form constant
    (−√6·L/32, missing μ₀ and wrong coefficient). This version uses
    the numerically exact direct solve which is always correct.

    Returns w ∈ ℝ³.
    Claim: [G] (exact for regular tetrahedron + Biot-Savart + centroid)
    """
    V = make_vertices(L)
    F0 = field_at_centroid(V)
    F0M = F0 @ tk.M.astype(float)
    return np.linalg.solve(F0M, np.asarray(B_target, dtype=float))


def compute_field(w: np.ndarray, u_coil: np.ndarray,
                  r: np.ndarray, V: np.ndarray) -> np.ndarray:
    """
    Compute B(r) = F(r) · (M·w + G·u_coil).
    Returns B vector in Tesla.
    """
    I = tk.M.astype(float) @ w + tk.G.astype(float) @ u_coil
    F = field_matrix(r, V)
    return F @ I


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    verify_layer4(verbose=True)
    print()
    verify_e_field(verbose=True)
