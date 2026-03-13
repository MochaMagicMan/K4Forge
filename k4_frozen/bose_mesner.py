"""
bose_mesner.py — Layer 5: Bose-Mesner Algebra {αI + βJ}
=========================================================

On C₃ symmetry axes, ALL cycle-space operators commute with S₃
permutations and therefore live in the 2D commutative algebra
spanned by I₃ and J₃ = ones(3,3).

KEY RESULTS:
  - Every operator = αI + βJ, characterized by two numbers
  - Eigenvalues: λ_br = α+3β (breathing), λ_diff = α (differential×2)
  - Condition number: R = 1+3β/α, κ = √max(R,1/R)
  - κ=1 at centroid (β=0), grows toward vertices
  - β/α has NO closed-form along C₃ (transcendental Biot-Savart)
  - Padé approximation KILLED (92% error at t=0.5)

SYMMETRY: Axis-adapted commutant is with respect to the C₃ stabilizer
(S₃ action on 3 remaining vertices). Full S₄-equivariance on the
6-edge space is a separate, stronger check.

SCOPE: Exact for symmetry-equivariant operators on C₃ axes of the
regular tetrahedron. Elsewhere, (α,β) are a best-fit projection and
ε is the honesty meter measuring departure from the algebra.
On C₂ axes at t=0.5, ε ≈ 0.41.

Claim class: [G] on C₃ axes, [M] off C₃
Frozen from Session 2026-02-27
"""

import numpy as np
from numpy.linalg import eigvalsh, norm
from typing import Tuple, Dict, Optional
from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# ALGEBRA OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def ab_multiply(a1: float, b1: float, a2: float, b2: float) -> Tuple[float, float]:
    """Multiply two operators in (α,β) representation.
    (α₁I+β₁J)(α₂I+β₂J) = (α₁α₂)I + (α₁β₂+β₁α₂+3β₁β₂)J"""
    return (a1 * a2, a1 * b2 + b1 * a2 + 3 * b1 * b2)


def ab_inverse(a: float, b: float) -> Tuple[float, float]:
    """Inverse of αI+βJ in the algebra.
    Solve (a,b)·(a',b') = (1,0): a' = 1/a, b' = -b/(a(a+3b))"""
    if abs(a) < 1e-30:
        raise ValueError("α=0: operator is proportional to J, not invertible")
    lbr = a + 3 * b
    if abs(lbr) < 1e-30:
        raise ValueError("α+3β=0: breathing eigenvalue is zero, not invertible")
    return (1.0 / a, -b / (a * lbr))


def ab_eigenvalues(a: float, b: float) -> Tuple[float, float]:
    """Return (λ_breathing, λ_differential) eigenvalues."""
    return (a + 3 * b, a)


def ab_kappa(a: float, b: float) -> float:
    """Condition number from (α,β).
    R = 1 + 3β/α, κ = √max(R, 1/R).
    Returns inf if α=0."""
    if abs(a) < 1e-30:
        return float('inf')
    R = 1.0 + 3.0 * b / a
    if R <= 0:
        return float('inf')
    return np.sqrt(max(R, 1.0 / R))


def ab_from_matrix(A: np.ndarray) -> Tuple[float, float, float]:
    """Extract (α, β, ε) from a 3×3 symmetric matrix.
    α = diagonal - off-diagonal (average)
    β = off-diagonal (average)
    ε = norm of residual A - (αI+βJ), measuring departure from algebra.
    """
    diag_mean = np.mean(np.diag(A))
    off_diag = []
    for i in range(3):
        for j in range(3):
            if i != j:
                off_diag.append(A[i, j])
    off_mean = np.mean(off_diag)
    alpha = diag_mean - off_mean
    beta = off_mean
    residual = A - (alpha * np.eye(3) + beta * np.ones((3, 3)))
    eps = norm(residual) / max(norm(A), 1e-30)
    return (alpha, beta, eps)


def ab_from_matrix_axis_adapted(A: np.ndarray, axis: np.ndarray) -> Tuple[float, float, float]:
    """Extract (α, β, ε) adapted to a specific C₃ axis direction.

    Rotates A into a frame where the C₃ axis is [1,1,1]/√3,
    then extracts (α,β,ε). This is REQUIRED for correct extraction
    on non-[1,1,1] C₃ axes. Without it, ε appears nonzero even on C₃.

    axis: unit vector along C₃ (e.g., vertex direction / √3)
    """
    # Build orthonormal basis: axis, then two perpendicular
    axis = axis / norm(axis)
    # Find a perpendicular vector
    if abs(axis[0]) < 0.9:
        v1 = np.cross(axis, [1, 0, 0])
    else:
        v1 = np.cross(axis, [0, 1, 0])
    v1 /= norm(v1)
    v2 = np.cross(axis, v1)
    R = np.column_stack([v1, v2, axis])  # rotation matrix

    # Rotate A into axis-adapted frame
    A_rot = R.T @ A @ R

    return ab_from_matrix(A_rot)


# ═══════════════════════════════════════════════════════════════════
# OPERATOR CATALOG
# ═══════════════════════════════════════════════════════════════════

CATALOG = {
    "I":          (1.0, 0.0),
    "J":          (0.0, 1.0),
    "Gram":       (4.0, -1.0),
    "Gram_inv":   (0.25, 0.25),
    "Gram_sq":    (16.0, -5.0),
    "P_parallel": (0.0, 1.0/3.0),
    "P_perp":     (1.0, -1.0/3.0),
}


def print_catalog():
    """Print the full operator catalog."""
    print(f"  {'Operator':>15s} {'α':>8s} {'β':>8s} {'λ_br':>8s} {'λ_diff':>8s} {'κ':>8s}")
    print(f"  {'─'*55}")
    for name, (a, b) in CATALOG.items():
        lbr, ldiff = ab_eigenvalues(a, b)
        k = ab_kappa(a, b) if (abs(a) > 1e-30 and abs(lbr) > 1e-30) else float('inf')
        k_str = f"{k:.2f}" if k < 100 else "∞"
        print(f"  {name:>15s} {a:>8.4f} {b:>8.4f} {lbr:>8.4f} {ldiff:>8.4f} {k_str:>8s}")


# ═══════════════════════════════════════════════════════════════════
# CYCLE-FIELD OPERATOR A(r) = F(r)·P_C·F(r)^T
# ═══════════════════════════════════════════════════════════════════

def cycle_field_operator(r: np.ndarray, V: np.ndarray) -> np.ndarray:
    """Compute A(r) = F(r)·P_C·F(r)^T, the 3×3 cycle-space field response."""
    M_f = tk.M.astype(float)
    Gram_inv = tk.get_gram_inverse()
    P_C = M_f @ Gram_inv @ M_f.T
    F = fe.field_matrix(r, V)
    return F @ P_C @ F.T


def spectral_coordinates(r: np.ndarray, V: np.ndarray,
                         axis: Optional[np.ndarray] = None) -> Dict:
    """
    Full spectral diagnostic at point r.

    Returns dict with:
      alpha, beta, epsilon: Bose-Mesner coordinates
      kappa: condition number
      eigenvalues: sorted array
      lambda_br, lambda_diff: algebra eigenvalues
      on_algebra: bool (ε < 1e-6)
    """
    A = cycle_field_operator(r, V)
    eigs = sorted(eigvalsh(A))

    if axis is not None:
        alpha, beta, eps = ab_from_matrix_axis_adapted(A, axis)
    else:
        alpha, beta, eps = ab_from_matrix(A)

    lbr, ldiff = ab_eigenvalues(alpha, beta)
    # Use analytical κ only when matrix is genuinely in the {αI+βJ} algebra.
    # At ε > 1e-3, the matrix has departed significantly from the algebra
    # and the analytical formula is unreliable — fall back to direct SVD.
    kappa = ab_kappa(alpha, beta) if eps < 1e-3 else np.sqrt(eigs[-1] / max(eigs[0], 1e-30))

    return {
        'alpha': alpha, 'beta': beta, 'epsilon': eps,
        'kappa': kappa,
        'eigenvalues': np.array(eigs),
        'lambda_br': lbr, 'lambda_diff': ldiff,
        'on_algebra': eps < 1e-6,
    }


# ═══════════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def verify_bose_mesner(verbose: bool = True) -> Dict[str, bool]:
    """Verify all Bose-Mesner algebra claims."""
    results = {}
    V = fe.make_vertices()

    # V2.BM1: Algebra multiplication consistency
    # Gram · Gram⁻¹ = I in (α,β)
    a, b = ab_multiply(4.0, -1.0, 0.25, 0.25)
    results["BM1_gram_times_inv"] = abs(a - 1.0) < 1e-14 and abs(b) < 1e-14

    # V2.BM2: Gram² = Gram·Gram
    a2, b2 = ab_multiply(4.0, -1.0, 4.0, -1.0)
    results["BM2_gram_squared"] = abs(a2 - 16.0) < 1e-14 and abs(b2 + 5.0) < 1e-14

    # V2.BM3: Inverse formula
    ai, bi = ab_inverse(4.0, -1.0)
    results["BM3_inverse_formula"] = abs(ai - 0.25) < 1e-14 and abs(bi - 0.25) < 1e-14

    # V2.BM4: κ at centroid = 1
    c = fe.centroid(V)
    sc = spectral_coordinates(c, V, axis=np.array([1, 1, 1.0]))
    results["BM4_centroid_kappa_1"] = abs(sc['kappa'] - 1.0) < 1e-6

    # V2.BM5: ε = 0 at centroid
    results["BM5_centroid_on_algebra"] = sc['on_algebra']

    # V2.BM6: All 4 C₃ axes give same κ at t=0.5
    kappas = []
    for vi in range(4):
        axis = V[vi] / norm(V[vi])
        r = 0.5 * axis * norm(V[vi])
        sc_v = spectral_coordinates(r, V, axis=axis)
        kappas.append(sc_v['kappa'])
    results["BM6_S4_equivalence"] = np.std(kappas) / np.mean(kappas) < 1e-10

    # V2.BM7: κ monotonically increases centroid → vertex on C₃
    ts = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
    axis = V[0] / norm(V[0])
    ks = []
    for t in ts:
        r = t * V[0]
        sc_t = spectral_coordinates(r, V, axis=axis)
        ks.append(sc_t['kappa'])
    results["BM7_kappa_monotone"] = all(ks[i] <= ks[i + 1] + 1e-10 for i in range(len(ks) - 1))

    # V2.BM8: Eigenvalue catalog consistency
    for name, (a_cat, b_cat) in CATALOG.items():
        mat = a_cat * np.eye(3) + b_cat * np.ones((3, 3))
        eigs = sorted(eigvalsh(mat))
        lbr_expected = a_cat + 3 * b_cat
        ldiff_expected = a_cat
        ok = abs(eigs[-1] - max(lbr_expected, ldiff_expected)) < 1e-10
        results[f"BM8_catalog_{name}"] = ok

    if verbose:
        print("=" * 60)
        print("BOSE-MESNER ALGEBRA VERIFICATION")
        print("=" * 60)
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")
        p = sum(results.values())
        n = len(results)
        print(f"\n  {p}/{n} tests passed")

    return results


if __name__ == "__main__":
    verify_bose_mesner()
