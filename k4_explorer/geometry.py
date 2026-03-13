"""
k4_explorer.geometry — Geometry Adapter
========================================

Maps physical realizations into frozen control coordinates.
This is the bridge between hardware-space and theorem-space.

DOCTRINE:
    Physical realizations do not alter the frozen control language.
    Every realization maps to canonical (w, u_coil, u) via this adapter.
    Adapter outputs declare approximation class and symmetry deviations.

IMPORT RULES:
    May import: k4_frozen.truth_kernel, k4_frozen.field_engine, contracts
    Must never import: k4_explorer.solver, k4_explorer.optimizer
"""

import numpy as np
from typing import Optional

from .contracts import (
    GeometrySpec, SymmetryClass, ClaimClass, ConfigID,
)


def adapt_regular(L: float = 0.1,
                  wire_radius: float = 0.0,
                  config_id: ConfigID = ConfigID.D) -> GeometrySpec:
    """
    Construct a GeometrySpec for an ideal regular tetrahedron.

    This is the canonical geometry. claim_ceiling = [G].

    Parameters:
        L: edge length in meters (default 0.1 = 10 cm)
        wire_radius: conductor radius in meters (0 = filament model)
        config_id: hardware configuration
    """
    from k4_frozen import field_engine as fe

    V = fe.make_vertices(L)

    # Verify regularity: all 6 edge lengths should equal L
    edges = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    lengths = [np.linalg.norm(V[i] - V[j]) for i, j in edges]
    max_deviation = max(abs(l - L) for l in lengths) / L
    assert max_deviation < 1e-12, f"Vertex construction not regular: max deviation {max_deviation}"

    # Verify centroid at origin
    centroid = V.mean(axis=0)
    assert np.linalg.norm(centroid) < 1e-14, f"Centroid not at origin: {centroid}"

    return GeometrySpec(
        vertices=V,
        edge_length=L,
        symmetry_class=SymmetryClass.Td_REGULAR,
        wire_radius=wire_radius,
        config_id=config_id,
        symmetry_deviations={"max_edge_deviation": float(max_deviation)},
        broken_assumptions=(),
    )


def adapt_irregular(vertices: np.ndarray,
                    wire_radius: float = 0.0,
                    config_id: ConfigID = ConfigID.D) -> GeometrySpec:
    """
    Construct a GeometrySpec for a non-ideal tetrahedron.

    claim_ceiling = [M]. F₀·G ≠ 0 in general.
    The frozen truth kernel (M, G, D) still holds — those are graph properties.
    What changes is the field matrix F(r).
    """
    assert vertices.shape == (4, 3), f"Expected (4,3) vertices, got {vertices.shape}"

    edges = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    lengths = [np.linalg.norm(vertices[i] - vertices[j]) for i, j in edges]
    mean_L = np.mean(lengths)
    max_deviation = max(abs(l - mean_L) for l in lengths) / mean_L

    # Classify symmetry
    if max_deviation < 0.001:
        sym = SymmetryClass.Td_APPROX
        broken = ()
    elif max_deviation < 0.5:
        sym = SymmetryClass.IRREGULAR
        broken = ("T_d symmetry (F0·G ≠ 0)", "κ(F0M) ≠ 2")
    else:
        sym = SymmetryClass.DEGENERATE
        broken = ("T_d symmetry", "centroid properties", "E-field uniformity")

    return GeometrySpec(
        vertices=vertices,
        edge_length=float(mean_L),
        symmetry_class=sym,
        wire_radius=wire_radius,
        config_id=config_id,
        symmetry_deviations={"max_edge_deviation": float(max_deviation)},
        broken_assumptions=broken,
    )
