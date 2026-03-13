"""
spherical_harmonics.py — Layer 6: K₄ as l=1 Spherical Harmonic Synthesizer
============================================================================

DISCOVERIES (Session 2026-02-27):
  - 3-phase [cos(ωt), cos(ωt-120°), cos(ωt+120°)] → perfect circle ⊥ [1,1,1]
  - (1, ω, ω²) is S-eigenvector with λ = -1-i√3, |λ|=2
  - Breathing (m=0) and rotation (m=±1) DECOUPLED at centroid
  - Response |S·w|² = 4 - (Σwᵢ)² (l=0 ⊕ l=2, no l≥3)
  - K₄ cycle space = complete l=1 spherical harmonic basis

SCOPE: Centroid results are exact (to machine precision).
Off-centroid on C₃ axes: circle holds. Off C₃: ellipse.

Claim class: [G] at centroid, [M] off-centroid
Frozen from Session 2026-02-27
"""

import numpy as np
from numpy.linalg import norm, svd
from typing import Tuple, Dict
from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# FUNDAMENTAL EIGENVECTORS OF S
# ═══════════════════════════════════════════════════════════════════

# S eigenvalues and eigenvectors
# λ₁ = -1         → [1,1,1] (breathing, m=0)
# λ₂ = -1-i√3     → (1, ω, ω²) (rotation, m=+1)
# λ₃ = -1+i√3     → (1, ω², ω) (rotation, m=-1)
# where ω = exp(-2πi/3)

OMEGA = np.exp(-2j * np.pi / 3)
BREATHING_VEC = np.array([1, 1, 1], dtype=float) / np.sqrt(3)
ROTATION_VEC = np.array([1, OMEGA, OMEGA**2])  # complex
ROTATION_RE = ROTATION_VEC.real
ROTATION_IM = ROTATION_VEC.imag
AXIS_HAT = BREATHING_VEC  # [1,1,1]/√3 is the rotation axis


# ═══════════════════════════════════════════════════════════════════
# MODE DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════

def decompose_mode(w: np.ndarray) -> Dict:
    """
    Decompose cycle weights w into breathing and rotation components.

    Returns dict with:
      breathing_amp: amplitude along [1,1,1]/√3
      rotation_amp: amplitude in plane ⊥ [1,1,1]
      rotation_phase: phase angle in equatorial plane (radians)
      breathing_frac: fraction of energy in breathing
      rotation_frac: fraction in rotation
    """
    w = np.asarray(w, dtype=float)
    br = np.dot(w, BREATHING_VEC)  # projection onto [1,1,1]/√3
    w_perp = w - br * BREATHING_VEC

    rot_amp = norm(w_perp)
    if rot_amp > 1e-30:
        # Phase relative to Re(v_rot)
        re_comp = np.dot(w_perp, ROTATION_RE / norm(ROTATION_RE))
        im_comp = np.dot(w_perp, ROTATION_IM / norm(ROTATION_IM))
        phase = np.arctan2(im_comp, re_comp)
    else:
        phase = 0.0

    total_sq = norm(w)**2
    br_frac = br**2 / total_sq if total_sq > 0 else 0
    rot_frac = rot_amp**2 / total_sq if total_sq > 0 else 0

    return {
        'breathing_amp': br,
        'rotation_amp': rot_amp,
        'rotation_phase': phase,
        'breathing_frac': br_frac,
        'rotation_frac': rot_frac,
    }


def three_phase(t: float, omega: float = 1.0) -> np.ndarray:
    """Standard 3-phase waveform: [cos(ωt), cos(ωt-120°), cos(ωt+120°)]."""
    return np.array([
        np.cos(omega * t),
        np.cos(omega * t - 2 * np.pi / 3),
        np.cos(omega * t + 2 * np.pi / 3),
    ])


def dc_breathing(amplitude: float = 1.0) -> np.ndarray:
    """Pure breathing mode: equal currents in all face loops."""
    return amplitude * BREATHING_VEC * np.sqrt(3)  # unnormalized: [a, a, a]


def response_magnitude_sq(w: np.ndarray) -> float:
    """Compute |S·w|² = 4|w|² - (Σwᵢ)² for arbitrary w."""
    S = tk.S.astype(float)
    Sw = S @ w
    return np.dot(Sw, Sw)


def response_on_sphere(w_hat: np.ndarray) -> float:
    """For unit w, compute |S·w|² = 4 - (w₁+w₂+w₃)².
    This is the response function on the input sphere S²."""
    return 4.0 - (w_hat[0] + w_hat[1] + w_hat[2])**2


# ═══════════════════════════════════════════════════════════════════
# FIELD TRACE ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def trace_field(wfn, T: float, n_points: int, V: np.ndarray,
                r: np.ndarray = None) -> Dict:
    """
    Trace B-field over one period for a time-varying waveform.

    wfn: callable t → w (3-vector of cycle weights)
    T: period
    n_points: number of sample points
    V: vertex array
    r: observation point (default: centroid)

    Returns dict with:
      B_trace: (n_points, 3) array of B-vectors
      magnitudes: |B| at each timestep
      circularity: std/mean of |B| (0 = perfect circle)
      plane_normal: normal to the best-fit plane of the trace
      plane_alignment: |dot(plane_normal, [1,1,1]/√3)|
    """
    if r is None:
        r = fe.centroid(V)

    F = fe.field_matrix(r, V)
    M_f = tk.M.astype(float)
    FM = F @ M_f  # 3×3

    ts = np.linspace(0, T, n_points, endpoint=False)
    B_trace = np.array([FM @ wfn(t) for t in ts])
    mags = norm(B_trace, axis=1)

    circularity = mags.std() / mags.mean() if mags.mean() > 0 else 0

    # SVD to find plane normal
    B_centered = B_trace - B_trace.mean(axis=0)
    U, sig, Vt = svd(B_centered)
    plane_normal = Vt[-1]  # smallest singular value direction
    plane_alignment = abs(np.dot(plane_normal, AXIS_HAT))

    return {
        'B_trace': B_trace,
        'magnitudes': mags,
        'circularity': circularity,
        'plane_normal': plane_normal,
        'plane_alignment': plane_alignment,
        'mean_magnitude': mags.mean(),
        'std_magnitude': mags.std(),
    }


# ═══════════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def verify_spherical_harmonics(verbose: bool = True) -> Dict[str, bool]:
    """Verify all spherical harmonic claims."""
    results = {}
    V = fe.make_vertices()
    S = tk.S.astype(float)

    # V2.SH1: (1,ω,ω²) is S-eigenvector
    Sv = S @ ROTATION_VEC
    ratio = Sv / ROTATION_VEC
    results["SH1_eigenvector"] = np.allclose(ratio, ratio[0], atol=1e-12)

    # V2.SH2: eigenvalue is -1-i√3
    lam = ratio[0]
    results["SH2_eigenvalue"] = (abs(lam.real + 1) < 1e-12 and
                                  abs(abs(lam.imag) - np.sqrt(3)) < 1e-12)

    # V2.SH3: S·[1,1,1] = -[1,1,1]
    Sb = S @ np.array([1, 1, 1], dtype=float)
    results["SH3_breathing_eigenvalue"] = np.allclose(Sb, -np.ones(3), atol=1e-14)

    # V2.SH4: 3-phase → constant |B| (perfect circle)
    trace = trace_field(three_phase, 2 * np.pi, 360, V)
    results["SH4_circular_field"] = trace['circularity'] < 1e-14

    # V2.SH5: Circle plane ⊥ [1,1,1]
    results["SH5_plane_alignment"] = trace['plane_alignment'] > 1 - 1e-6

    # V2.SH6: Breathing/rotation decoupling
    S_br = S @ BREATHING_VEC
    S_re = S @ ROTATION_RE
    S_im = S @ ROTATION_IM
    results["SH6_decouple_re"] = abs(np.dot(S_br, S_re)) < 1e-14
    results["SH6_decouple_im"] = abs(np.dot(S_br, S_im)) < 1e-14

    # V2.SH7: Response function |S·w|² = 4|w|² - (Σwᵢ)²
    np.random.seed(42)
    for trial in range(10):
        w = np.random.randn(3)
        actual = norm(S @ w)**2
        formula = 4 * norm(w)**2 - (w.sum())**2
        if abs(actual - formula) > 1e-10:
            results["SH7_response_formula"] = False
            break
    else:
        results["SH7_response_formula"] = True

    # V2.SH8: On unit sphere, response = 4 - (Σwᵢ)² (no l≥3)
    # Sample random unit vectors, verify
    for trial in range(10):
        w = np.random.randn(3)
        w /= norm(w)
        actual = norm(S @ w)**2
        formula = 4.0 - w.sum()**2
        if abs(actual - formula) > 1e-10:
            results["SH8_unit_sphere_response"] = False
            break
    else:
        results["SH8_unit_sphere_response"] = True

    # V2.SH9: Off-centroid on C₃: still circular
    r_off = 0.3 * V[0]  # on C₃(V₀) axis
    trace_off = trace_field(three_phase, 2 * np.pi, 360, V, r=r_off)
    results["SH9_offcenter_circular"] = trace_off['circularity'] < 1e-10

    # V2.SH10: Mode decomposition consistency
    w_test = np.array([1.0, 0.5, -0.3])
    mode = decompose_mode(w_test)
    results["SH10_mode_energy_partition"] = abs(mode['breathing_frac'] + mode['rotation_frac'] - 1.0) < 1e-10

    if verbose:
        print("=" * 60)
        print("SPHERICAL HARMONIC VERIFICATION")
        print("=" * 60)
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")
        p = sum(results.values())
        n = len(results)
        print(f"\n  {p}/{n} tests passed")

    return results


if __name__ == "__main__":
    verify_spherical_harmonics()
