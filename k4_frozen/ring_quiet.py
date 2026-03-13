"""
k4_frozen_v3.ring_quiet — Ring-Quiet Operating Mode
=====================================================

A ring-quiet mode exists where the three base (ring) edges of a
chosen face carry exactly zero current while the three spoke (apex)
edges carry all field-producing current.

Key results:
  T2.3: Ring-quiet ⟺ w₁+w₂+w₃ = 0 (balanced cycle condition)  [A]
  Ring edge cancellation is algebraic (exact), not tuned.

Applications:
  - Sensing on silent edges (no self-interference)
  - Component isolation (dead edges don't heat)
  - Fault compensation (route around failed edges)
  - MHD flow concentration in spoke tubes
"""

import numpy as np
from typing import Dict, NamedTuple, List
from . import truth_kernel as tk
from . import field_engine as fe


class RingQuietSolution(NamedTuple):
    """Complete ring-quiet mode specification."""
    w: np.ndarray           # cycle weights (balanced: sum = 0)
    u_coil: np.ndarray      # cut weights (ring cancellation)
    I_edge: np.ndarray      # 6 edge currents
    I_cycle: np.ndarray     # cycle contribution per edge
    I_cut: np.ndarray       # cut contribution per edge
    active_edges: List[str] # labels of edges carrying current
    silent_edges: List[str] # labels of edges with I = 0
    B_centroid: np.ndarray  # field at centroid from these currents


def compute_ring_quiet(w_balanced: np.ndarray,
                       face_idx: int = 0,
                       L: float = fe.DEFAULT_L) -> RingQuietSolution:
    """
    Compute ring-quiet mode for a given balanced cycle weight vector.
    
    The balanced condition w₁+w₂+w₃ = 0 is REQUIRED.
    Given w, find u_coil such that ring edges carry zero total current.
    
    For Config V₀ (face_idx=0), ring edges are E12, E23, E31 (indices 3,4,5).
    These are the edges of face F₀ = {V₁,V₂,V₃}.
    
    The solution is: u_coil chosen so (G·u_coil)|_ring = −(M·w)|_ring.
    
    Claim: [A] (algebraic identity from M, G structure)
    """
    w = np.asarray(w_balanced, dtype=float)
    
    # Verify balance
    balance = abs(np.sum(w))
    if balance > 1e-10:
        raise ValueError(f"Cycle weights must be balanced (sum=0), got sum={np.sum(w):.6f}")
    
    Mf = tk.M.astype(float)
    Gf = tk.G.astype(float)
    
    # Ring edges for face 0: E12(idx 3), E13(idx 4), E23(idx 5)
    ring_idx = [3, 4, 5]
    apex_idx = [0, 1, 2]
    
    # Cycle contribution on ring edges
    I_cycle_ring = (Mf @ w)[ring_idx]
    
    # We need: G_ring · u_coil = −M_ring · w
    G_ring = Gf[ring_idx, :]  # 3×3 submatrix (rank 2, singular!)
    
    # G_ring is singular (rank 2). But for balanced w, the RHS is
    # in the column space of G_ring (Theorem T2.3). Use lstsq.
    # NOTE: lstsq returns minimum-norm solution. Physically, this
    # corresponds to the gauge choice V₀ = 0 (one vertex grounded).
    # If hardware uses a different ground reference, add an explicit
    # gauge constraint: e.g., pin u_coil[0] = 0 and solve the 2×2.
    u_coil, residuals, rank, sv = np.linalg.lstsq(G_ring, -I_cycle_ring, rcond=None)
    
    # Verify the residual is zero (it must be for balanced w)
    actual_residual = np.linalg.norm(G_ring @ u_coil + I_cycle_ring)
    if actual_residual > 1e-10:
        raise RuntimeError(f"Ring cancellation failed: residual = {actual_residual:.2e}. "
                          f"Is w balanced? sum(w) = {np.sum(w):.6f}")
    
    # Full edge currents
    I_cycle_full = Mf @ w
    I_cut_full = Gf @ u_coil
    I_total = I_cycle_full + I_cut_full
    
    # Verify ring edges are zero
    ring_residual = np.max(np.abs(I_total[ring_idx]))
    if ring_residual > 1e-8:
        raise RuntimeError(f"Ring cancellation failed: max residual = {ring_residual:.2e}")
    
    # Compute B at centroid
    V = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V)
    B = F0 @ I_total
    
    labels = tk.EDGE_LABELS
    active = [labels[k] for k in apex_idx if abs(I_total[k]) > 1e-10]
    silent = [labels[k] for k in ring_idx]
    
    return RingQuietSolution(
        w=w, u_coil=u_coil,
        I_edge=I_total, I_cycle=I_cycle_full, I_cut=I_cut_full,
        active_edges=active, silent_edges=silent,
        B_centroid=B,
    )


def canonical_vortex_mode(L: float = fe.DEFAULT_L) -> RingQuietSolution:
    """
    The canonical vortex ring-quiet mode:
      w = [1, −½, −½]  (balanced: 1 − ½ − ½ = 0)
      
    This produces a vortex-like current pattern with the apex
    vertex (V₀) as the circulation center.
    """
    return compute_ring_quiet(np.array([1.0, -0.5, -0.5]), face_idx=0, L=L)


def verify_ring_quiet(verbose: bool = False) -> bool:
    """
    Verify ring-quiet mode properties.
    
    Tests:
    1. Ring edges carry exactly zero current (algebraic)
    2. B at centroid is nonzero (field is still produced)
    3. Balanced condition is necessary
    4. Multiple balanced vectors all work
    """
    all_pass = True
    
    if verbose:
        print("Ring-Quiet Mode Verification:")
    
    # Test 1: Canonical vortex mode
    sol = canonical_vortex_mode()
    ring_zero = np.max(np.abs(sol.I_edge[[3, 4, 5]])) < 1e-14
    B_nonzero = np.linalg.norm(sol.B_centroid) > 1e-10
    
    all_pass = all_pass and ring_zero and B_nonzero
    
    if verbose:
        print(f"\n  Canonical vortex: w = {sol.w}")
        print(f"  u_coil = {sol.u_coil}")
        print(f"  Edge currents:")
        for k, label in enumerate(tk.EDGE_LABELS):
            status = "SILENT" if abs(sol.I_edge[k]) < 1e-10 else "ACTIVE"
            print(f"    {label}: {sol.I_edge[k]:+8.4f} A  (cyc: {sol.I_cycle[k]:+.4f}, cut: {sol.I_cut[k]:+.4f})  [{status}]")
        print(f"  Ring zero: {'✓' if ring_zero else '✗'}")
        print(f"  |B| at centroid: {np.linalg.norm(sol.B_centroid)*1e6:.2f} μT  {'✓' if B_nonzero else '✗'}")
    
    # Test 2: Other balanced vectors
    test_vectors = [
        np.array([0.5, 0.5, -1.0]),
        np.array([2.0, -1.0, -1.0]),
        np.array([0.3, -0.1, -0.2]),
    ]
    for w in test_vectors:
        sol = compute_ring_quiet(w)
        ring_ok = np.max(np.abs(sol.I_edge[[3, 4, 5]])) < 1e-12
        all_pass = all_pass and ring_ok
        if verbose:
            print(f"  w={w}: ring zero = {'✓' if ring_ok else '✗'}")
    
    # Test 3: Unbalanced should fail
    try:
        compute_ring_quiet(np.array([1.0, 0.0, 0.0]))
        unbalanced_caught = False
    except ValueError:
        unbalanced_caught = True
    
    all_pass = all_pass and unbalanced_caught
    if verbose:
        print(f"  Unbalanced rejection: {'✓' if unbalanced_caught else '✗'}")
    
    return all_pass


if __name__ == "__main__":
    verify_ring_quiet(verbose=True)
