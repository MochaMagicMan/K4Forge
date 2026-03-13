"""
k4_explorer.context — FieldContext Construction
=================================================

Builds the FieldContext bridge object from frozen modules.
This is the ONLY place where k4_frozen.field_engine is called
by the exploration layer.

IMPORT RULES:
    May import: k4_frozen.truth_kernel, k4_frozen.field_engine, contracts
    Must never import: k4_explorer.solver, k4_explorer.optimizer
"""

import numpy as np
from functools import partial

from .contracts import FieldContext, GeometrySpec, ClaimClass, SymmetryClass


def build_context(spec: GeometrySpec) -> FieldContext:
    """
    Build a FieldContext from a GeometrySpec.

    This function is the bridge. It calls into k4_frozen to construct
    the precomputed field matrices, then wraps them in a FieldContext
    that the solver can use without touching k4_frozen directly.

    The FieldContext carries its own quality metrics so the solver
    knows what claim class is safe.
    """
    from k4_frozen import truth_kernel as tk
    from k4_frozen import field_engine as fe
    from k4_frozen import check_populated
    check_populated()

    V = spec.vertices
    L = spec.edge_length
    M = tk.M.astype(np.int64)
    G = tk.G.astype(np.int64)

    # Compute centroid field matrix
    F0 = fe.field_at_centroid(V)
    F0M = F0 @ M.astype(float)
    F0G = F0 @ G.astype(float)

    # Quality check: F0 @ G should be ≈ 0 for Td geometries
    F0G_residual = float(np.max(np.abs(F0G)))

    # Centroid inversion matrix (direct solve — NOT the closed-form with wrong coefficient)
    F0M_inv = np.linalg.inv(F0M)
    F0M_condition = float(np.linalg.cond(F0M))

    # E-field volume matrix (barycentric model)
    E_vol = fe.e_field_volume_matrix(V)

    # Determine claim ceiling based on geometry quality
    if spec.symmetry_class == SymmetryClass.Td_REGULAR:
        if F0G_residual < 1e-12 and abs(F0M_condition - 2.0) < 0.01:
            ceiling = ClaimClass.G
        else:
            ceiling = ClaimClass.M  # something unexpected — downgrade
    else:
        ceiling = spec.claim_ceiling

    # Callable for arbitrary-point field evaluation
    def _field_matrix_at(r: np.ndarray) -> np.ndarray:
        return fe.field_matrix(r, V)

    return FieldContext(
        V=V,
        L=L,
        F0=F0,
        F0M=F0M,
        F0M_inv=F0M_inv,
        F0G=F0G,
        E_vol=E_vol,
        M=M,
        G=G,
        field_matrix_at=_field_matrix_at,
        F0G_residual=F0G_residual,
        F0M_condition=F0M_condition,
        claim_ceiling=ceiling,
    )
