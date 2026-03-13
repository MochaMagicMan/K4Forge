"""
k4_explorer.drive — DriveSpec Construction and Verification
==============================================================

Physical realization of Hodge coordinates into hardware signals.
Verifies decomposition invariants.

IMPORT RULES:
    May import: k4_explorer.contracts, k4_frozen.truth_kernel (for M, G)
    Must never import: k4_frozen.field_engine
"""

import numpy as np
from .contracts import DriveSpec, FrequencyRegime


def verify_drive(drive: DriveSpec, M: np.ndarray, G: np.ndarray,
                 tol: float = 1e-12) -> bool:
    """Verify DriveSpec invariant: I_edge == M @ w + G @ u_coil."""
    return drive.verify_decomposition(M, G, tol)


def decompose_edge_currents(I_edge: np.ndarray,
                             M: np.ndarray,
                             G: np.ndarray) -> tuple:
    """
    Decompose arbitrary I_edge into (w, u_coil).

    Uses pseudoinverse: w = M⁺ @ I, u_coil = G⁺ @ I.
    Exact because M⁺ @ G = 0 and G⁺ @ M = 0.
    """
    Mf = M.astype(float)
    Gf = G.astype(float)
    MtM_inv = np.linalg.inv(Mf.T @ Mf)
    GtG_inv = np.linalg.inv(Gf.T @ Gf)
    w = MtM_inv @ Mf.T @ I_edge
    u_coil = GtG_inv @ Gf.T @ I_edge
    return w, u_coil
