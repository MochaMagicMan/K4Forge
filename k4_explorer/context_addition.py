# ═══════════════════════════════════════════════════════════════════
# PHYSICAL REALIZATION → FIELD CONTEXT
# ═══════════════════════════════════════════════════════════════════
#
# Append this to the end of context.py, after build_context().
# This is the second entry point: instead of ideal Biot-Savart,
# it uses the actual segment geometry from a PhysicalRealization.
#
# The existing build_context(GeometrySpec) path is unchanged.

from .contracts import PhysicalRealization, EdgeModel


def build_context_from_realization(real: PhysicalRealization) -> FieldContext:
    """
    Build a FieldContext from a PhysicalRealization.

    This replaces ideal single-wire Biot-Savart with the actual coil
    geometry (bundled wire, solenoid, etc). Everything downstream
    (solver, observables, viewports) works unchanged because they
    see the same FieldContext interface.

    The key difference from build_context(GeometrySpec):
    - field_matrix_at uses physical segments, not ideal wire
    - F0 is computed from physical geometry
    - claim_ceiling may be lower
    - Current normalization is applied per the realization's wiring spec
    """
    from k4_frozen import truth_kernel as tk
    from k4_frozen import field_engine as fe
    from k4_frozen import check_populated
    check_populated()

    V = real.vertices
    M = tk.M.astype(np.int64)
    G = tk.G.astype(np.int64)

    # Bind the Biot-Savart function from the frozen core
    def _biot_savart(P1, P2, r, I):
        return fe.biot_savart_segment(P1, P2, r, I)

    # Compute centroid field matrix using physical geometry
    c = V.mean(axis=0)
    F0 = real.field_matrix_at(c, _biot_savart)
    F0M = F0 @ M.astype(float)
    F0G = F0 @ G.astype(float)

    # Quality check
    F0G_residual = float(np.max(np.abs(F0G)))
    rank_FM = np.linalg.matrix_rank(F0M, tol=1e-10)

    if rank_FM < 3:
        raise ValueError(
            f"rank(F0·M) = {rank_FM} < 3 — cycle spanning lost for "
            f"realization '{real.description}'. Cannot build valid FieldContext. "
            f"Check coil geometry or vertex positions."
        )

    F0M_inv = np.linalg.inv(F0M)
    F0M_condition = float(np.linalg.cond(F0M))

    # E-field model is geometry-independent (barycentric, from vertices)
    E_vol = fe.e_field_volume_matrix(V)

    # Run validation to get claim ceiling
    validation = real.validate(_biot_savart, M, G)
    ceiling = validation["overall_ceiling"]

    # Build the field evaluator callable (closes over the realization)
    def _field_matrix_at(r: np.ndarray) -> np.ndarray:
        return real.field_matrix_at(r, _biot_savart)

    return FieldContext(
        V=V,
        L=real.characteristic_length,
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
