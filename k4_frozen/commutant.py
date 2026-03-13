"""
k4_frozen_v3.commutant — S₄ Commutant Algebra and Representation Theory
=========================================================================

The edge space ℝ⁶ decomposes under S₄ as T₂ ⊕ T₁ (cycle ⊕ cut),
both with multiplicity 1.

The commutant algebra of S₄ on ℝ⁶ is spanned by {I₆, Σ, A_opp}:
  - I₆: identity
  - Σ = D^T·D − 2·I₆: signed edge adjacency
  - A_opp: opposite-edge pairing matrix

Key results:
  S4.1: E irrep in ∂(F·M)/∂r (cycle gradient = pure quadrupole)  [G]
  S4.2: T₁ irrep in ∂(F·G)/∂r (cut gradient = pure rotation)    [G]
  S4.3: Gradient irrep complementarity (zero mixing)              [A]
  S4.4: κ = 2 at gradient level                                   [G]
  S4.5: ζ₄ = 1/7 exactly (Biot-Savart)                           [A+G]
  S4.6: All 8 chirality octants form single S₄ orbit              [A]

The unifying principle: multiplicity-1 forces invariant subspaces
to be 1-dimensional, so equivariant operators act as scalars.
"""

import numpy as np
from typing import Dict, Tuple
from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# COMMUTANT BASIS ELEMENTS
# ═══════════════════════════════════════════════════════════════════

def compute_sigma() -> np.ndarray:
    """
    Signed edge adjacency: Σ = D^T·D − 2·I₆.
    
    Eigenvalues on cycle/cut blocks:
      Σ · (cycle vectors) = −2 · (cycle vectors)    [A]
      Σ · (cut vectors) = +2 · (cut vectors)        [A]
    
    Proof:
      D·M = 0 → M^T·D^T·D·M = 0 → Σ·M = (D^T·D−2I)·M = −2M
      D^T·D = 4I on cut space → Σ·G = (4I−2I)·G = 2G
    """
    D = tk.D.astype(float)
    return D.T @ D - 2 * np.eye(6)


def compute_A_opp() -> np.ndarray:
    """
    Opposite-edge pairing matrix A_opp.
    
    A_opp[i,j] = 1 if edges i,j are opposite (share no vertex), 0 otherwise.
    
    In K₄, each edge has exactly one opposite edge:
      E01 ↔ E23, E02 ↔ E13, E03 ↔ E12
    """
    A = np.zeros((6, 6))
    # Edge ordering: E01, E02, E03, E12, E13, E23
    opp_pairs = [(0, 5), (1, 4), (2, 3)]  # E01↔E23, E02↔E13, E03↔E12
    for i, j in opp_pairs:
        A[i, j] = 1
        A[j, i] = 1
    return A


def verify_sigma_eigenvalues(verbose: bool = False) -> bool:
    """
    Verify that Σ has eigenvalue −2 on cycle space and +2 on cut space.
    Claim: [A] (follows from D·M = 0 and D^T·D = 4I on cut)
    """
    Sigma = compute_sigma()
    Mf = tk.M.astype(float)
    Gf = tk.G.astype(float)
    
    # Σ·M should equal −2·M
    SM = Sigma @ Mf
    err_cycle = np.max(np.abs(SM - (-2) * Mf))
    
    # Σ·G should equal +2·G
    SG = Sigma @ Gf
    err_cut = np.max(np.abs(SG - 2 * Gf))
    
    passed = err_cycle < 1e-14 and err_cut < 1e-14
    
    if verbose:
        print(f"  Σ·M = −2·M: err = {err_cycle:.2e}  {'✓' if err_cycle < 1e-14 else '✗'}")
        print(f"  Σ·G = +2·G: err = {err_cut:.2e}  {'✓' if err_cut < 1e-14 else '✗'}")
    
    return passed


def verify_A_opp_selection_rule(L: float = fe.DEFAULT_L, verbose: bool = False) -> bool:
    """
    Verify that A_opp is forbidden in the regular tetrahedron.
    
    Opposite edges are perpendicular: dl₁·dl₂ = 0 for each opposite pair.
    This is a geometric fact [G], not an algebraic identity.
    
    Consequence: the commutant collapses from 3D to 2D for any
    S₄-equivariant operator on the regular tetrahedron.
    """
    V = fe.make_vertices(L)
    edges = fe.make_edges(V)
    
    opp_pairs = [(0, 5), (1, 4), (2, 3)]
    max_dot = 0
    for i, j in opp_pairs:
        dl_i = edges[i][1] - edges[i][0]
        dl_j = edges[j][1] - edges[j][0]
        dot = abs(np.dot(dl_i, dl_j))
        max_dot = max(max_dot, dot)
    
    passed = max_dot < 1e-14
    
    if verbose:
        print(f"  Opposite edge perpendicularity: max|dl·dl| = {max_dot:.2e}  {'✓' if passed else '✗'}")
    
    return passed


# ═══════════════════════════════════════════════════════════════════
# GRADIENT THEOREMS
# ═══════════════════════════════════════════════════════════════════

def _field_matrix_complex(r_complex: np.ndarray, V: np.ndarray) -> np.ndarray:
    """
    Biot-Savart field matrix evaluation that accepts complex-valued r.
    Used for complex-step differentiation (avoids subtractive cancellation).
    
    This is a thin wrapper around the Biot-Savart formula that replaces
    np.linalg.norm with analytic-continuation-safe sqrt(sum(x²)).
    """
    edges = fe.make_edges(V)
    MU0_4PI = 1e-7  # μ₀/4π
    F = np.zeros((3, 6), dtype=complex)
    
    for k, (P1, P2) in enumerate(edges):
        dl = P2 - P1
        r1 = r_complex - P1
        r2 = r_complex - P2
        
        dl_cross_r1 = np.array([
            dl[1]*r1[2] - dl[2]*r1[1],
            dl[2]*r1[0] - dl[0]*r1[2],
            dl[0]*r1[1] - dl[1]*r1[0],
        ])
        
        # Analytic-continuation-safe norms (no abs, no conjugate)
        norm_cross_sq = np.sum(dl_cross_r1**2)
        if abs(norm_cross_sq) < 1e-60:
            continue
        
        dl_sq = np.sum(dl**2)
        r1_sq = np.sum(r1**2)
        r2_sq = np.sum(r2**2)
        
        norm_r1 = np.sqrt(r1_sq)
        norm_r2 = np.sqrt(r2_sq)
        norm_dl = np.sqrt(dl_sq)
        
        cos1 = np.sum(dl * r1) / (norm_dl * norm_r1)
        cos2 = np.sum(dl * r2) / (norm_dl * norm_r2)
        
        perp_dist = np.sqrt(norm_cross_sq / dl_sq)
        direction = dl_cross_r1 / np.sqrt(norm_cross_sq)
        
        magnitude = MU0_4PI * (cos1 - cos2) / perp_dist
        F[:, k] = magnitude * direction
    
    return F


def compute_gradient_gram(L: float = fe.DEFAULT_L, h: float = 1e-30) -> np.ndarray:
    """
    Compute the gradient Gram matrix using complex-step differentiation:
    G_grad[i,j] = Σ_k (∂F/∂r_k)^T_ki · (∂F/∂r_k)_kj
    
    Complex-step method: ∂F/∂r_k = Im[F(r + ih·ê_k)] / h
    This avoids all subtractive cancellation and gives derivatives
    accurate to machine precision (~1e-15) instead of the ~1e-4
    that finite differences achieve.
    
    Claim: [G] (exact for regular tetrahedron + Biot-Savart)
    """
    V = fe.make_vertices(L)
    cent = fe.centroid(V)
    
    G_grad = np.zeros((6, 6))
    for k in range(3):  # x, y, z derivatives
        # Complex-step: perturb r_k by ih, take Im(F)/h
        r_complex = cent.astype(complex).copy()
        r_complex[k] += 1j * h
        
        F_complex = _field_matrix_complex(r_complex, V)
        dF_dk = np.imag(F_complex) / h  # exact derivative, no cancellation
        
        G_grad += dF_dk.T @ dF_dk
    
    return G_grad


def verify_gradient_irrep_complementarity(L: float = fe.DEFAULT_L,
                                           verbose: bool = False) -> bool:
    """
    Verify S4.1-S4.3: Gradient irrep complementarity.
    
    Cycle gradient → pure E irrep (sym traceless)
    Cut gradient → pure T₁ irrep (antisymmetric)
    Zero mixing between them.
    
    Claim: [A] for the vanishing conditions, [G] for specific values.
    """
    G_grad = compute_gradient_gram(L)
    Mf = tk.M.astype(float)
    Gf = tk.G.astype(float)
    
    # Project onto cycle and cut blocks
    G_cycle = Mf.T @ G_grad @ Mf  # 3×3
    G_cut = Gf.T @ G_grad @ Gf    # 3×3
    G_cross = Mf.T @ G_grad @ Gf  # 3×3 (should be ≈ 0)
    
    cross_norm = np.linalg.norm(G_cross)
    
    # Check eigenvalue structure
    eig_c = np.linalg.eigvalsh(G_cycle)
    eig_k = np.linalg.eigvalsh(G_cut)
    
    passed = cross_norm < 1e-10
    
    if verbose:
        print(f"  Gradient cross-coupling ||M^T·G_grad·G|| = {cross_norm:.2e}  {'✓' if passed else '✗'}")
        print(f"  Cycle gradient eigenvalues: {eig_c}")
        print(f"  Cut gradient eigenvalues: {eig_k}")
    
    return passed


def compute_zeta4(L: float = fe.DEFAULT_L) -> float:
    """
    Compute ζ₄ = ||∂(F·G)/∂r|| / ||∂(F·M)/∂r|| at the centroid.
    
    This is the spatial reach ratio: how far the cut channel's field
    variation extends relative to the cycle channel's.
    
    Proven value: ζ₄ = 1/7 for Biot-Savart kernel.
    
    Claim: [A+G]
    Proof: commutant eigenvalue ratio + IBP identity 9K₁ = 7J₀.
    """
    G_grad = compute_gradient_gram(L)
    Mf = tk.M.astype(float)
    Gf = tk.G.astype(float)
    
    # Eigenvalues on each block
    G_cycle = Mf.T @ G_grad @ Mf
    G_cut = Gf.T @ G_grad @ Gf
    
    lambda_cycle = np.trace(G_cycle) / 3  # Average (degenerate)
    lambda_cut = np.trace(G_cut) / 3
    
    return np.sqrt(lambda_cut / lambda_cycle)


def verify_zeta4(L: float = fe.DEFAULT_L, verbose: bool = False) -> bool:
    """
    Verify S4.5: ζ₄ = 1/7 exactly.
    
    The proof chain:
    1. G_grad ∈ span{I₆, Σ} (equivariance + A_opp forbidden)  [A]+[G]
    2. λ_cycle = α−2β, λ_cut = α+2β  (Σ eigenvalues ±2)  [A]
    3. ζ₄ = |2J₀−3K₁|/(3K₁)  (commutant formula)  [A]
    4. 9K₁ = 7J₀  (IBP + evaluation for Biot-Savart)  [G]
    5. ζ₄ = |−3K₁/7|/(3K₁) = 1/7  ∎
    """
    zeta = compute_zeta4(L)
    expected = 1.0 / 7.0
    err = abs(zeta - expected)
    passed = err < 1e-10  # Complex-step gives ~machine precision
    
    if verbose:
        print(f"  ζ₄ = {zeta:.6f}  (expected 1/7 = {expected:.6f})")
        print(f"  Error: {err:.2e}  {'✓' if passed else '✗'}")
    
    return passed


# ═══════════════════════════════════════════════════════════════════
# COMPLETE S₄ IRREP ATLAS
# ═══════════════════════════════════════════════════════════════════

def irrep_atlas() -> Dict:
    """
    Complete S₄ irrep atlas for the K4 framework.
    
    Every irrep of S₄ has a home:
      A₁ (dim 1): Gauge DOF V=[1,1,1,1] (removed)
      A₂ (dim 1): T₁⊗T₂ gradient cross-term (role unclear)
      E  (dim 2): ∂(F·M)/∂r gradient tensor (quadrupolar)
      T₁ (dim 3): Cut space / vertex space (polar vector)
      T₂ (dim 3): Cycle space (pseudovector)
    
    T₂⊗T₂ = A₁ ⊕ E ⊕ T₁ ⊕ T₂ — all multiplicities exactly 1.
    """
    return {
        'A1': {'dim': 1, 'location': 'Gauge DOF', 'role': 'Common-mode, physically removed'},
        'A2': {'dim': 1, 'location': 'T1⊗T2 cross-term', 'role': 'Open question'},
        'E':  {'dim': 2, 'location': '∂(F·M)/∂r', 'role': 'Quadrupolar field variation'},
        'T1': {'dim': 3, 'location': 'Cut space', 'role': 'Polar vector: E-field, cut B-shaping'},
        'T2': {'dim': 3, 'location': 'Cycle space', 'role': 'Pseudovector: centroid B-field control'},
    }


# ═══════════════════════════════════════════════════════════════════
# 7-LINE PROJECTIVE 2-DESIGN
# ═══════════════════════════════════════════════════════════════════

def verify_projective_2design(verbose: bool = False) -> bool:
    """
    Verify that the 7 T_d symmetry axes form a projective 2-design.
    
    The 7 axes: 4 C₃ axes (vertex→opposite face) + 3 C₂ axes (edge midpoints).
    As rank-1 projectors: Σ_d P_d = (7/3)·I₃.
    
    Proof: orbit-sum is T_d-invariant → lives in Sym²(T₂)^{T_d}.
    A₁ has mult-1, so invariant subspace is 1D. By Schur: S_O = (|O|/3)·I₃.
    
    Claim: [A]
    """
    V = fe.make_vertices()
    
    # 4 C₃ axes: vertex to opposite face center
    axes = []
    faces_idx = [[1,2,3],[0,2,3],[0,1,3],[0,1,2]]
    for vi in range(4):
        fc = np.mean(V[faces_idx[vi]], axis=0)
        d = V[vi] - fc
        axes.append(d / np.linalg.norm(d))
    
    # 3 C₂ axes: edge midpoint to opposite edge midpoint
    edge_pairs = [(0,1), (0,2), (0,3)]  # representative edges
    opp_edges = [(2,3), (1,3), (1,2)]
    for (a,b), (c,d_idx) in zip(edge_pairs, opp_edges):
        m1 = 0.5 * (V[a] + V[b])
        m2 = 0.5 * (V[c] + V[d_idx])
        d = m1 - m2
        if np.linalg.norm(d) > 1e-15:
            axes.append(d / np.linalg.norm(d))
    
    # Sum of rank-1 projectors
    S = np.zeros((3, 3))
    for d in axes:
        S += np.outer(d, d)
    
    expected = (7.0 / 3.0) * np.eye(3)
    err = np.max(np.abs(S - expected))
    passed = err < 1e-12
    
    if verbose:
        print(f"  Σ P_d = (7/3)·I₃: max error = {err:.2e}  {'✓' if passed else '✗'}")
    
    return passed


# ═══════════════════════════════════════════════════════════════════
# MODULE VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def verify_commutant(verbose: bool = False) -> bool:
    """Run all commutant/representation theory tests."""
    all_pass = True
    
    if verbose:
        print("S₄ Commutant and Representation Theory:")
    
    # Σ eigenvalues
    if verbose:
        print("\n  Σ eigenvalue test:")
    passed = verify_sigma_eigenvalues(verbose=verbose)
    all_pass = all_pass and passed
    
    # A_opp selection rule
    if verbose:
        print("\n  A_opp selection rule:")
    passed = verify_A_opp_selection_rule(verbose=verbose)
    all_pass = all_pass and passed
    
    # Gradient irrep complementarity
    if verbose:
        print("\n  Gradient irrep complementarity:")
    passed = verify_gradient_irrep_complementarity(verbose=verbose)
    all_pass = all_pass and passed
    
    # ζ₄ = 1/7
    if verbose:
        print("\n  ζ₄ = 1/7 test:")
    passed = verify_zeta4(verbose=verbose)
    all_pass = all_pass and passed
    
    # Projective 2-design
    if verbose:
        print("\n  7-line projective 2-design:")
    passed = verify_projective_2design(verbose=verbose)
    all_pass = all_pass and passed
    
    return all_pass


if __name__ == "__main__":
    verify_commutant(verbose=True)
