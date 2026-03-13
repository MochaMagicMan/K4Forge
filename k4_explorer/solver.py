"""
k4_explorer.solver — Field Solve: Intention → DriveSpec
========================================================

Takes a ControlSpec + FieldContext and produces a DriveSpec.
Uses the centroid inversion (direct solve via F0M_inv) and
SVD-based least-squares for multi-constraint problems.

CRITICAL: Uses F0M_inv from FieldContext (the direct solve).
NEVER calls the closed-form centroid_inversion() which has the wrong coefficient.

IMPORT RULES:
    May import: k4_explorer.context, k4_explorer.contracts, k4_frozen.truth_kernel (for M, G)
    Must never import: k4_frozen.field_engine directly (use context)
"""

import numpy as np
from typing import Tuple

from .contracts import (
    ControlSpec, DriveSpec, FieldContext, ClaimClass, FrequencyRegime,
)


def solve_dc(spec: ControlSpec, ctx: FieldContext) -> DriveSpec:
    """
    Solve a DC static field request.

    Pipeline:
        1. B_target at centroid → w via (F0·M)⁻¹ (3 DOF, exact for regular K4)
        2. E_target → u_vertex via E_vol⁻¹ (3 DOF, independent)
        3. null_point → augmented least-squares (uses remaining DOF)
        4. I_edge = M·w + G·u_coil
        5. Verify: F0 @ I_edge ≈ B_target
    """
    M = ctx.M.astype(float)
    G = ctx.G.astype(float)

    # ── Step 1: Centroid B → cycle weights ──
    if spec.B_target is not None:
        B_target = np.array(spec.B_target, dtype=float)
        # Direct solve: w = (F0·M)⁻¹ · B_target
        w = ctx.F0M_inv @ B_target
    else:
        B_target = None
        w = np.zeros(3)

    # ── Step 2: E target → vertex potentials ──
    if spec.E_target is not None:
        E_target = np.array(spec.E_target, dtype=float)
        # E = -E_vol · u → u = -E_vol⁻¹ · E
        u_vertex = -np.linalg.solve(ctx.E_vol, E_target)
    else:
        u_vertex = np.zeros(3)

    # ── Step 3: Null / probe constraints → cut-coil weights ──
    u_coil = np.zeros(3)

    if spec.null_point is not None or len(spec.probe_targets) > 0:
        u_coil, w = _solve_constrained(spec, ctx, w)

    # ── Step 4: Reconstruct edge currents ──
    I_edge = M @ w + G @ u_coil

    # ── Step 5: Verify ──
    if B_target is not None:
        B_achieved = ctx.F0 @ I_edge
        B_error = float(np.linalg.norm(B_achieved - B_target))
        B_mag = float(np.linalg.norm(B_target))
        B_error_rel = B_error / B_mag if B_mag > 0 else 0.0
    else:
        B_error_rel = 0.0

    # ── Power budget (DC: V = R·I, P = R·ΣI²) ──
    # Use copper resistivity for default wire
    R_edge = _edge_resistance(ctx.L, max(spec.wire_radius_override if hasattr(spec, 'wire_radius_override') else 0, 5e-4))
    V_drive = R_edge * I_edge
    P_diss = R_edge * float(np.sum(I_edge**2))

    drive = DriveSpec(
        w=w,
        u_coil=u_coil,
        u_vertex=u_vertex,
        I_edge=I_edge,
        V_drive=V_drive,
        P_dissipated=P_diss,
        P_reactive=0.0,
        I_max=float(np.max(np.abs(I_edge))),
        V_max=float(np.max(np.abs(V_drive))),
        frequency=0.0,
        regime=FrequencyRegime.DC,
    )

    # Verify decomposition invariant
    assert drive.verify_decomposition(ctx.M, ctx.G), \
        "FATAL: I_edge != M @ w + G @ u_coil — decomposition invariant violated"

    return drive


def _solve_constrained(spec: ControlSpec, ctx: FieldContext,
                       w_initial: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Solve for (u_coil, w) when spatial constraints exist beyond centroid B.

    Uses stacked constraint matrix + SVD least-squares.
    Returns (u_coil, w_updated).
    """
    M = ctx.M.astype(float)
    G = ctx.G.astype(float)

    constraint_rows = []
    target_values = []

    # Centroid B constraint (if present)
    if spec.B_target is not None:
        constraint_rows.append(ctx.F0)  # (3, 6)
        target_values.append(np.array(spec.B_target, dtype=float))

    # Null constraint: B(r_null) = 0
    if spec.null_point is not None:
        r_null = np.array(spec.null_point, dtype=float)
        F_null = ctx.field_matrix_at(r_null)
        constraint_rows.append(F_null)  # (3, 6)
        target_values.append(np.zeros(3))

    # Probe constraints
    for probe in spec.probe_targets:
        r_probe = np.array(probe.position, dtype=float)
        F_probe = ctx.field_matrix_at(r_probe)
        constraint_rows.append(F_probe)
        target_values.append(np.array(probe.B_target, dtype=float))

    # Stack: A @ I_edge = b
    A = np.vstack(constraint_rows)     # (3k, 6)
    b = np.concatenate(target_values)  # (3k,)

    # Solve via least-squares
    I_sol, residuals, rank, sv = np.linalg.lstsq(A, b, rcond=None)

    # Decompose I_sol back into Hodge coordinates
    # w = M⁺ · I, u_coil = G⁺ · I (exact because M⁺@G = 0, G⁺@M = 0)
    MtM_inv = np.linalg.inv(M.T @ M)
    GtG_inv = np.linalg.inv(G.T @ G)
    w_out = MtM_inv @ M.T @ I_sol
    u_coil_out = GtG_inv @ G.T @ I_sol

    return u_coil_out, w_out


def _edge_resistance(L: float, wire_radius: float) -> float:
    """Resistance per edge, copper, DC."""
    rho_cu = 1.68e-8  # Ohm·m
    A = np.pi * wire_radius**2
    return rho_cu * L / A if A > 0 else 1.0
