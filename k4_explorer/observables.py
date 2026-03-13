"""
k4_explorer.observables — Observable Evaluation
=================================================

Evaluates field quantities at viewports and arbitrary points.
Decomposes B into cycle and cut contributions.

IMPORT RULES:
    May import: k4_explorer.context, k4_explorer.contracts
    Must never import: k4_explorer.solver
"""

import numpy as np
from typing import List, Optional

from .contracts import (
    ObservableBundle, DriveSpec, FieldContext, ClaimClass,
)

# ═══════════════════════════════════════════════════════════════════
# CANONICAL VIEWPORT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

# Viewport positions as functions of L and V (vertices).
# These match the Doctrine Viewport Atlas (VP-01 through VP-09).

def _viewport_positions(ctx: FieldContext) -> dict:
    """Compute canonical viewport positions for this geometry."""
    V = ctx.V
    L = ctx.L
    c = V.mean(axis=0)  # centroid (should be origin for regular)

    # Face centers
    face_center_0 = (V[1] + V[2] + V[3]) / 3  # opposite V0

    # Vertex axis direction (V0 → centroid extended)
    v0_dir = c - V[0]
    v0_hat = v0_dir / np.linalg.norm(v0_dir) if np.linalg.norm(v0_dir) > 0 else np.array([0, 0, 1])

    # Edge midpoints
    edge_mid_01 = (V[0] + V[1]) / 2

    return {
        "VP-01": c,                                    # Centroid
        "VP-02": c + 0.05 * L * v0_hat,               # Shell 0.05L from centroid
        "VP-03": face_center_0,                        # Face center (F0)
        "VP-04": c + 0.3 * L * v0_hat,                # Vertex axis 0.3L
        "VP-05": c + 0.6 * L * v0_hat,                # Vertex axis 0.6L
        "VP-06": edge_mid_01,                          # Edge midpoint E01
        "VP-07": c + 1.0 * L * np.array([1, 0, 0]),   # Exterior 1L
        "VP-08": c + 3.0 * L * np.array([1, 0, 0]),   # Exterior 3L
        "VP-09": c + 0.1 * L * np.array([1, 0, 0]),   # Null ring 0.1L
    }


def evaluate_at_point(r: np.ndarray,
                      drive: DriveSpec,
                      ctx: FieldContext,
                      viewport_id: Optional[str] = None) -> ObservableBundle:
    """
    Evaluate all observables at a single point.

    Decomposes B into cycle and cut contributions:
        B_cycle = F(r) · M · w
        B_cut   = F(r) · G · u_coil
        B_total = B_cycle + B_cut = F(r) · I_edge
    """
    M = ctx.M.astype(float)
    G = ctx.G.astype(float)

    F_r = ctx.field_matrix_at(r)

    B_total = F_r @ drive.I_edge
    B_cycle = F_r @ (M @ drive.w)
    B_cut = F_r @ (G @ drive.u_coil)

    B_mag = float(np.linalg.norm(B_total))
    B_cyc_mag = float(np.linalg.norm(B_cycle))
    B_cut_mag = float(np.linalg.norm(B_cut))
    selectivity = B_cyc_mag / B_cut_mag if B_cut_mag > 1e-30 else float('inf')

    # E-field (only meaningful inside the tetrahedron)
    # Simple check: is point inside by barycentric test? For now, compute if u_vertex nonzero.
    E = None
    if np.any(np.abs(drive.u_vertex) > 1e-15):
        E = ctx.E_vol @ drive.u_vertex

    # Claim class depends on position
    if viewport_id == "VP-01":
        claim = ctx.claim_ceiling  # centroid: highest available
    else:
        claim = ClaimClass.M  # off-centroid: model-dependent

    return ObservableBundle(
        position=r.copy(),
        viewport_id=viewport_id,
        B_total=B_total,
        B_cycle=B_cycle,
        B_cut=B_cut,
        B_magnitude=B_mag,
        E=E,
        selectivity=selectivity,
        claim_class=claim,
        model_notes=f"Biot-Savart thin-wire, L={ctx.L}m",
    )


def evaluate_viewports(drive: DriveSpec,
                       ctx: FieldContext,
                       viewport_ids: Optional[List[str]] = None) -> List[ObservableBundle]:
    """
    Evaluate observables at all (or selected) canonical viewports.

    Returns a list of ObservableBundles, one per viewport.
    """
    positions = _viewport_positions(ctx)

    if viewport_ids is None:
        viewport_ids = sorted(positions.keys())

    results = []
    for vp_id in viewport_ids:
        if vp_id not in positions:
            raise ValueError(f"Unknown viewport: {vp_id}. Valid: {sorted(positions.keys())}")
        r = positions[vp_id]
        obs = evaluate_at_point(r, drive, ctx, viewport_id=vp_id)
        results.append(obs)

    return results
