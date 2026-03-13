"""
integration.py — Docking Specification for K₄ Extensions
==========================================================

THE EXPLICIT CONTRACT for anything that wants to claim K₄ properties
without being an ideal regular tetrahedron.

Covers:
  - Non-ideal (irregular) single tetrahedra
  - Multi-cell K₄ arrays (planar, volumetric)
  - Bundle geometries (racetrack coils, hypertoroids)
  - External coupling (plasma, workpiece interaction)

Every extension must:
  1. Obtain a GeometryCertification (from policy.py)
  2. Declare its ConfigID and model tier
  3. Accept the claim ceiling that follows
  4. Provide a calibrated F-matrix if claiming field control

The frozen stack's truth_kernel (M, G, D) is ALWAYS valid regardless
of geometry — that's the whole point of Layer 0-1. What changes under
non-ideal geometry is Layer 3-4: the field matrix F(r) and the
selection rules that depend on it.

Frozen at: K4 Definitive Reference v1.2.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from . import truth_kernel as tk
from . import field_engine as fe
from .session_schema import ConfigID, BModelTier, ClaimClass
from .policy import GeometryCertification, claim_ceiling


# ═══════════════════════════════════════════════════════════════════
# WHAT ALWAYS HOLDS (regardless of geometry)
# ═══════════════════════════════════════════════════════════════════
#
# These are Layer 0-1 facts. They cannot break:
#
#   M^T · G = 0         (cycle ⊥ cut in ℝ⁶)
#   D · M = 0           (cycles satisfy KCL)
#   P_cycle + P_cut = I₆ (projection completeness)
#   I = M·w + G·u       (every current decomposes uniquely)
#
# These hold because they are properties of K₄ the GRAPH,
# not of any physical embedding. Even if your tetrahedron is
# squashed, bent, or made of spaghetti.


# ═══════════════════════════════════════════════════════════════════
# WHAT CHANGES (under non-ideal geometry)
# ═══════════════════════════════════════════════════════════════════
#
# Layer 3-4 results depend on the physical embedding:
#
#   F₀·G = 0       ← requires T_d symmetry at evaluation point
#   rank(F₀·M) = 3 ← requires non-degenerate geometry
#   κ(F₀·M) = 2    ← requires regular tetrahedron
#
# For irregular tetrahedra:
#   - F₀·G ≈ 0 (approximately, not exactly)
#   - rank(F₀·M) = 3 (almost certainly, unless badly degenerate)
#   - κ(F₀·M) ≠ 2 (depends on specific shape)
#
# The system STILL WORKS — it just needs calibration.
# M and G are still the correct bases. F is what changes.


# ═══════════════════════════════════════════════════════════════════
# CALIBRATED FIELD MATRIX
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CalibratedFieldMatrix:
    """
    A field matrix obtained from measurement or high-fidelity simulation
    rather than the ideal Biot-Savart model.

    This is the bridge between the frozen algebraic core and real hardware.
    """
    # Identity
    description: str = ""
    geometry_cert: Optional[GeometryCertification] = None

    # The matrix itself
    F_matrix: Optional[np.ndarray] = None  # 3×6 at one point
    evaluation_point: Optional[np.ndarray] = None  # where F was measured
    evaluation_label: str = ""  # "centroid", "face_0", etc.

    # Calibration metadata
    source: str = ""         # "biot_savart", "FEM", "measurement", "comsol"
    b_model_tier: BModelTier = BModelTier.FINITE_SEGMENT_BIOT_SAVART
    date: str = ""
    uncertainty_estimate: Optional[float] = None  # ‖δF‖/‖F‖

    def validate(self) -> List[str]:
        """Check internal consistency."""
        warnings = []
        if self.F_matrix is None:
            warnings.append("No F matrix provided")
            return warnings

        if self.F_matrix.shape != (3, 6):
            warnings.append(f"F matrix shape {self.F_matrix.shape} ≠ (3,6)")

        # Check cut annihilation (should be near-zero for centroid)
        G_f = tk.G.astype(float)
        FG = self.F_matrix @ G_f
        norm_FG = np.linalg.norm(FG)
        if norm_FG > 1e-10:
            warnings.append(
                f"‖F·G‖ = {norm_FG:.2e} — cut annihilation NOT exact at this point. "
                f"If this is the centroid of a regular tetrahedron, something is wrong. "
                f"If this is off-centroid or irregular geometry, this is expected."
            )

        # Check cycle spanning
        M_f = tk.M.astype(float)
        FM = self.F_matrix @ M_f
        rank_FM = np.linalg.matrix_rank(FM, tol=1e-10)
        if rank_FM < 3:
            warnings.append(
                f"rank(F·M) = {rank_FM} < 3 — cycle spanning LOST. "
                f"Cannot achieve full 3D B-control at this point."
            )

        return warnings

    def diagnostics(self) -> Dict:
        """Compute diagnostic quantities from the calibrated F."""
        if self.F_matrix is None:
            return {}

        G_f = tk.G.astype(float)
        M_f = tk.M.astype(float)
        FG = self.F_matrix @ G_f
        FM = self.F_matrix @ M_f

        svs_FM = np.linalg.svd(FM, compute_uv=False)
        svs_FG = np.linalg.svd(FG, compute_uv=False)

        return {
            "norm_FG": float(np.linalg.norm(FG)),
            "rank_FM": int(np.linalg.matrix_rank(FM, tol=1e-10)),
            "kappa_FM": float(svs_FM[0] / svs_FM[-1]) if svs_FM[-1] > 1e-30 else float('inf'),
            "singular_values_FM": svs_FM.tolist(),
            "singular_values_FG": svs_FG.tolist(),
            "cut_annihilation_dB": float(-20 * np.log10(np.linalg.norm(FG) / np.linalg.norm(FM)))
                if np.linalg.norm(FG) > 0 and np.linalg.norm(FM) > 0 else float('inf'),
            "max_claim_class": self._max_claim().value,
        }

    def _max_claim(self) -> ClaimClass:
        """What's the highest claim class results from this F can carry?"""
        if self.geometry_cert is not None:
            return self.geometry_cert.max_claim_class()
        if self.source == "measurement":
            return ClaimClass.H
        return ClaimClass.M


# ═══════════════════════════════════════════════════════════════════
# MULTI-CELL ARRAYS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class K4Cell:
    """One K₄ cell in a multi-cell array."""
    cell_id: str
    vertices: np.ndarray             # (4,3) vertex positions
    geometry_cert: GeometryCertification = None
    config_id: ConfigID = ConfigID.D

    def field_matrix_at(self, r: np.ndarray) -> np.ndarray:
        """Compute F(r) for this cell's geometry."""
        return fe.field_matrix(r, self.vertices)


@dataclass
class K4Array:
    """
    Multi-cell K₄ array.

    CRITICAL RULE: Each cell is an independent K₄ with its own M, G, D.
    The frozen matrices are the SAME for every cell (they're properties
    of K₄ the graph, not the embedding). What differs is:
      - Vertex positions (geometry)
      - F matrix (field contribution)
      - Coupling between cells (mutual inductance, shared vertices)

    Cell coupling is NOT part of the frozen stack. It requires:
      - Mutual inductance computation (Neumann integral)
      - Shared-vertex current conservation
      - Inter-cell field superposition

    These are all [M] or [H] claims.
    """
    cells: List[K4Cell] = field(default_factory=list)
    coupling_model: str = "none"  # "none", "superposition", "mutual_inductance"

    def add_cell(self, cell: K4Cell):
        self.cells.append(cell)

    def total_field_at(self, r: np.ndarray, currents: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute total B at point r from all cells.

        currents: {cell_id: I_vector (6,)} for each cell.
        Uses simple superposition (no mutual inductance correction).

        Claim: [M] (superposition is model-dependent)
        """
        B_total = np.zeros(3)
        for cell in self.cells:
            if cell.cell_id in currents:
                F = cell.field_matrix_at(r)
                B_total += F @ currents[cell.cell_id]
        return B_total

    def validate(self) -> List[str]:
        """Check array consistency."""
        warnings = []
        for cell in self.cells:
            if cell.geometry_cert is not None:
                w = cell.geometry_cert.validate()
                warnings.extend([f"Cell {cell.cell_id}: {m}" for m in w])
        return warnings


# ═══════════════════════════════════════════════════════════════════
# BUNDLE / HYPERTORROID MAPPING
# ═══════════════════════════════════════════════════════════════════

@dataclass
class BundleMapping:
    """
    Maps a physical coil bundle geometry to K₄ topology.

    A "bundle" is a physical implementation where each K₄ edge is
    realized by a coil (racetrack, solenoid, saddle, etc.) rather
    than a single wire. The bundle has:
      - Physical coil geometry (shape, turns, cross-section)
      - Equivalent K₄ edge (which edge does this coil implement?)
      - Effective wire path (for Biot-Savart or FEM)

    The mapping must satisfy:
      - Each K₄ edge maps to exactly one coil (or coil group)
      - Coil current direction matches the edge orientation convention
      - The resulting F matrix is computed from the actual coil geometry

    Claim class: [H] (hardware-dependent) unless measured, then [M].
    """
    edge_to_coil: Dict[str, str] = field(default_factory=dict)
    # e.g. {"E01": "racetrack_coil_A", "E02": "racetrack_coil_B", ...}

    coil_descriptions: Dict[str, str] = field(default_factory=dict)
    turns_per_coil: Dict[str, int] = field(default_factory=dict)

    def validate(self) -> List[str]:
        warnings = []
        # Must map all 6 edges
        required = set(tk.EDGE_LABELS)
        mapped = set(self.edge_to_coil.keys())
        missing = required - mapped
        if missing:
            warnings.append(f"Unmapped edges: {missing}. All 6 edges must be realized.")
        extra = mapped - required
        if extra:
            warnings.append(f"Extra edge mappings: {extra}. K₄ has exactly 6 edges.")
        return warnings


# ═══════════════════════════════════════════════════════════════════
# EXTENSION CHECKLIST
# ═══════════════════════════════════════════════════════════════════

EXTENSION_CHECKLIST = """
╔══════════════════════════════════════════════════════════════╗
║         K₄ EXTENSION CHECKLIST                              ║
║         Complete before claiming K₄ properties              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  □ 1. GEOMETRY CERTIFICATION                                ║
║       Create a GeometryCertification with:                  ║
║       - vertex_count = 4, edge_count = 6                    ║
║       - is_complete_graph = True                            ║
║       - Correct ConfigID                                     ║
║       - geometry_type (regular_K4 / irregular_K4 / ...)     ║
║       - calibration_required flag                           ║
║                                                              ║
║  □ 2. FIELD MATRIX                                          ║
║       Either:                                                ║
║       a) Use field_engine for regular K₄ (claim [G])        ║
║       b) Provide calibrated F from FEM/measurement ([M/H])  ║
║                                                              ║
║  □ 3. POLICY GATE                                           ║
║       Pass every SessionResult through policy.gate()        ║
║       Accept the auto-downgraded claim class                ║
║                                                              ║
║  □ 4. REGRESSION                                            ║
║       Run the 12-test regression on your geometry           ║
║       (some tests will fail for non-regular K₄ — expected)  ║
║                                                              ║
║  □ 5. DOCUMENT DEVIATIONS                                   ║
║       List every way your geometry departs from ideal:       ║
║       - Edge length variations                               ║
║       - Non-straight conductors                              ║
║       - Finite wire thickness                                ║
║       - Magnetic materials                                   ║
║       - Shared vertices with adjacent cells                  ║
║                                                              ║
║  □ 6. COUPLING MODEL (multi-cell only)                      ║
║       Specify: superposition / mutual inductance / FEM      ║
║       Tag all inter-cell results as [M] minimum             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(EXTENSION_CHECKLIST)

    print("=" * 60)
    print("INTEGRATION SELF-TEST")
    print("=" * 60)

    # Test 1: Calibrated F matrix for regular K₄
    V = fe.make_vertices()
    F0 = fe.field_at_centroid(V)
    cal = CalibratedFieldMatrix(
        description="Regular K₄ centroid",
        F_matrix=F0,
        evaluation_point=np.zeros(3),
        evaluation_label="centroid",
        source="biot_savart",
    )
    warnings = cal.validate()
    diag = cal.diagnostics()
    print(f"  Regular K₄ centroid F matrix:")
    print(f"    ‖F·G‖ = {diag['norm_FG']:.2e}")
    print(f"    rank(F·M) = {diag['rank_FM']}")
    print(f"    κ(F·M) = {diag['kappa_FM']:.4f}")
    print(f"    Cut annihilation: {diag['cut_annihilation_dB']:.0f} dB")
    print(f"    Warnings: {len(warnings)}")
    print(f"    {'✓ PASS' if len(warnings) == 0 else '✗ FAIL'}")

    # Test 2: Off-centroid F matrix (cut annihilation breaks)
    r_off = np.array([0.02, 0.0, 0.0])
    F_off = fe.field_matrix(r_off, V)
    cal_off = CalibratedFieldMatrix(
        description="Regular K₄ off-centroid",
        F_matrix=F_off,
        evaluation_point=r_off,
        source="biot_savart",
    )
    diag_off = cal_off.diagnostics()
    print(f"\n  Off-centroid (0.02m):")
    print(f"    ‖F·G‖ = {diag_off['norm_FG']:.2e}")
    print(f"    Cut annihilation: {diag_off['cut_annihilation_dB']:.1f} dB")
    print(f"    Max claim: [{diag_off['max_claim_class']}]")

    # Test 3: Bundle mapping validation
    bundle = BundleMapping(
        edge_to_coil={
            "E01": "coil_A", "E02": "coil_B", "E03": "coil_C",
            "E12": "coil_D", "E13": "coil_E",
            # Missing E23!
        }
    )
    bw = bundle.validate()
    print(f"\n  Incomplete bundle (5/6 edges):")
    print(f"    Violations: {len(bw)}")
    print(f"    {'✓ PASS (caught missing edge)' if len(bw) > 0 else '✗ FAIL'}")
