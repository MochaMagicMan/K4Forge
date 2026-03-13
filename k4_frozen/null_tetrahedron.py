"""
null_tetrahedron.py — The Null Tetrahedron Structure
=====================================================

KEY DISCOVERY: Each face center has exactly one invisible cut mode.
These four null directions form a second tetrahedron in cut-coordinate
space (the "null tetrahedron").

Properties:
  - Vertex V_i's injection is invisible at opposite face F_i
  - Simplex relation: u₀ = u₁ + u₂ + u₃ [A]
  - No two null directions are parallel [G]
  - Any 2 faces + centroid give full rank 6 [G]
  - Null directions SNAP on symmetry paths (don't interpolate) [G]

Claim classes: [A] algebraic, [G] geometric exact, [M] numerical
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# FACE NULL DIRECTIONS (exact, from symmetry analysis)
# ═══════════════════════════════════════════════════════════════════

# Null cut directions: u_i such that F_B(face_i_center) · G · u_i = 0
# These are EXACT for the regular tetrahedron under Biot-Savart [G]
FACE_NULL_DIRECTIONS = {
    "F0": np.array([1, 1, 1], dtype=float),  # opposite V0
    "F1": np.array([1, 0, 0], dtype=float),  # opposite V1
    "F2": np.array([0, 1, 0], dtype=float),  # opposite V2
    "F3": np.array([0, 0, 1], dtype=float),  # opposite V3
}

# Edge midpoint null directions: exact on C₂ symmetry axes [G]
EDGE_NULL_DIRECTIONS = {
    "E01_E23": np.array([0, 1, 1], dtype=float) / np.sqrt(2),  # opposite pair
    "E02_E13": np.array([1, 0, 1], dtype=float) / np.sqrt(2),
    "E03_E12": np.array([1, 1, 0], dtype=float) / np.sqrt(2),
}

# Vertex injection patterns: J_i = D · G · u_i [A]
VERTEX_INJECTIONS = {
    "V0": np.array([-3, +1, +1, +1], dtype=float),  # u = [1,1,1]
    "V1": np.array([-1, +3, -1, -1], dtype=float),  # u = [1,0,0]
    "V2": np.array([-1, -1, +3, -1], dtype=float),  # u = [0,1,0]
    "V3": np.array([-1, -1, -1, +3], dtype=float),  # u = [0,0,1]
}


# ═══════════════════════════════════════════════════════════════════
# SIMPLEX RELATION [A] — exact algebraic
# ═══════════════════════════════════════════════════════════════════

def verify_simplex_relation() -> bool:
    """
    Verify u₀ = u₁ + u₂ + u₃ (the 3-simplex relation).
    This is algebraic — no geometry needed. [A]
    """
    u0 = FACE_NULL_DIRECTIONS["F0"]
    u1 = FACE_NULL_DIRECTIONS["F1"]
    u2 = FACE_NULL_DIRECTIONS["F2"]
    u3 = FACE_NULL_DIRECTIONS["F3"]
    return np.allclose(u0, u1 + u2 + u3)


# ═══════════════════════════════════════════════════════════════════
# FACE SUFFICIENCY THEOREM [G]
# ═══════════════════════════════════════════════════════════════════

def face_sufficiency_analysis(L: float = fe.DEFAULT_L) -> Dict:
    """
    Verify: Any 2 faces + centroid give full rank 6.

    At centroid: rank(F₀·M) = 3 (cycle spanning, 3 DOF from w).
    Each face center adds rank(F_face·G projected onto null complement).
    Two faces eliminate 2D of the 3D cut null → full rank.

    Returns analysis dict with condition numbers for all 6 face pairs.
    Claim: [G]
    """
    V = fe.make_vertices(L)
    fc = fe.face_centers(V)
    c = fe.centroid(V)
    F0 = fe.field_at_centroid(V)
    G_f = tk.G.astype(float)
    M_f = tk.M.astype(float)

    # Centroid block: F₀·M (3×3, rank 3)
    F0M = F0 @ M_f

    results = {"pairs": {}}
    face_indices = [0, 1, 2, 3]

    for i in range(4):
        for j in range(i+1, 4):
            # Build augmented system: centroid B targets (3) + face B targets (6)
            Fi = fe.field_matrix(fc[i], V)
            Fj = fe.field_matrix(fc[j], V)

            # Full 9×6 system: [F₀; F_i; F_j] · I = targets
            A = np.vstack([F0, Fi, Fj])
            rank_A = np.linalg.matrix_rank(A, tol=1e-10)

            # Condition number of the 6×6 effective system (via SVD)
            svs = np.linalg.svd(A, compute_uv=False)
            svs_nonzero = svs[svs > 1e-14]
            kappa = svs_nonzero[0] / svs_nonzero[-1] if len(svs_nonzero) >= 6 else np.inf

            pair_name = f"F{i}+F{j}"
            results["pairs"][pair_name] = {
                "rank": rank_A,
                "condition": kappa,
                "full_rank": (rank_A == 6),
            }

    # Verify null direction pairwise non-parallel
    null_dirs = [FACE_NULL_DIRECTIONS[f"F{i}"] / np.linalg.norm(FACE_NULL_DIRECTIONS[f"F{i}"])
                 for i in range(4)]
    results["pairwise_nonparallel"] = True
    for i in range(4):
        for j in range(i+1, 4):
            cos_angle = abs(np.dot(null_dirs[i], null_dirs[j]))
            if cos_angle > 0.999:
                results["pairwise_nonparallel"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# NULL DIRECTION COMPUTATION AT ARBITRARY POINTS [M]
# ═══════════════════════════════════════════════════════════════════

def compute_null_direction(r: np.ndarray, V: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    At point r, find the cut direction u that minimizes ‖F(r)·G·u‖.

    Returns (null_direction, null_depth) where:
      - null_direction: unit vector in ℝ³ (cut-coordinate space)
      - null_depth: σ₃/σ₁ of F(r)·G (0 = perfect null)

    Claim: [M] (model-dependent numerical result)
    """
    F = fe.field_matrix(r, V)
    FG = F @ tk.G.astype(float)
    U, S, Vt = np.linalg.svd(FG)
    null_dir = Vt[-1]  # right singular vector for smallest σ
    null_depth = S[-1] / S[0] if S[0] > 1e-30 else 0.0
    return null_dir, null_depth


def null_tetrahedron_analysis(L: float = fe.DEFAULT_L,
                               verbose: bool = True) -> Dict[str, bool]:
    """
    Complete verification of the null tetrahedron structure.
    """
    V = fe.make_vertices(L)
    fc = fe.face_centers(V)
    em = fe.edge_midpoints(V)
    G_f = tk.G.astype(float)
    results = {}

    # 1. Verify face null directions [G]
    for i, fname in enumerate(["F0", "F1", "F2", "F3"]):
        u = FACE_NULL_DIRECTIONS[fname]
        F_face = fe.field_matrix(fc[i], V)
        FGu = F_face @ G_f @ u
        norm_FGu = np.linalg.norm(FGu)
        results[f"null_{fname}"] = (norm_FGu < 1e-12)

    # 2. Simplex relation [A]
    results["simplex_relation"] = verify_simplex_relation()

    # 3. Vertex injection patterns [A]
    D_f = tk.D.astype(float)
    for vname, expected_J in VERTEX_INJECTIONS.items():
        i = int(vname[1])
        u = FACE_NULL_DIRECTIONS[f"F{i}"]
        I_cut = G_f @ u
        J = D_f @ I_cut
        results[f"injection_{vname}"] = np.allclose(J, expected_J)

    # 4. Face sufficiency [G]
    suff = face_sufficiency_analysis(L)
    all_full_rank = all(v["full_rank"] for v in suff["pairs"].values())
    results["face_sufficiency_all_pairs"] = all_full_rank
    results["pairwise_nonparallel"] = suff["pairwise_nonparallel"]

    # 5. Edge midpoint null directions [G]
    opp_pairs = [(0, 5), (1, 4), (2, 3)]  # E01↔E23, E02↔E13, E03↔E12
    pair_names = ["E01_E23", "E02_E13", "E03_E12"]
    for (e1, e2), pname in zip(opp_pairs, pair_names):
        mid = em[e1]  # midpoint of first edge in pair
        computed_dir, depth = compute_null_direction(mid, V)
        expected_dir = EDGE_NULL_DIRECTIONS[pname]
        # Check alignment (up to sign)
        alignment = abs(np.dot(computed_dir, expected_dir))
        results[f"edge_null_{pname}"] = (alignment > 0.99)

    # 6. Centroid collapse: entire cut space is null [G]
    c = fe.centroid(V)
    F0G = fe.field_at_centroid(V) @ G_f
    results["centroid_full_cut_null"] = (np.linalg.norm(F0G) < 1e-14)

    if verbose:
        print("=" * 60)
        print("NULL TETRAHEDRON VERIFICATION")
        print("=" * 60)
        all_pass = True
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")
            if not passed:
                all_pass = False
        print()
        print("  Face sufficiency condition numbers:")
        for pair, data in suff["pairs"].items():
            print(f"    {pair}: rank={data['rank']}, κ={data['condition']:.1f}")
        p = sum(results.values())
        n = len(results)
        print(f"\n  {p}/{n} tests passed")

    return results


# ═══════════════════════════════════════════════════════════════════
# DOF ACCOUNTING (corrected inverse problem)
# ═══════════════════════════════════════════════════════════════════

DOF_TABLE = """
DOF Accounting [A]:
  6 edge currents → at most 6 scalar field values exactly.
  B at one point = 3 components.

  | Level | Obs Points      | Targets | Rank | Free DOF | Tag   |
  |-------|-----------------|---------|------|----------|-------|
  | 0     | Centroid        | 3       | 3    | 3 (cut)  | [G]   |
  | 1     | C + 1 face      | 6       | 5    | 1        | [G]   |
  | 1+    | C + 1 face opt  | 6       | 5    | 0 (cost) | [G/M] |
  | 2     | C + 2 faces     | 9       | 6    | 0 (l.s.) | [M]   |
"""


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    null_tetrahedron_analysis(verbose=True)
