"""
k4_explorer.contracts — Canonical Data Objects
================================================

Every cross-layer data transfer in the engine uses one of these types.
They are the passports through customs between layers.

IMPORT RULES:
    This module imports ONLY: numpy, typing, dataclasses, enum.
    It must NEVER import from k4_frozen or any k4_explorer logic module.
    Data objects are pure schemas — no computation.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# ENUMS — typed alternatives to free strings
# ═══════════════════════════════════════════════════════════════════

class ClaimClass(str, Enum):
    """
    Claim taxonomy. Every result carries one of these.

    [A]  Algebraic exact / unconditional. Integer(0) via SymPy.
    [G]  Geometric exact under named premises. Premises must be stated.
    [Gs] Model-limited analytic. Valid within stated regime only.
    [M]  Model-dependent numerical. Not a proof.
    [H]  Hardware / engineering heuristic.
    [C]  Conjectural / incomplete proof path.

    Promotion requires explicit action with a named proof.
    Demotion is always allowed and should be announced.
    """
    A  = "A"
    G  = "G"
    Gs = "G*"
    M  = "M"
    H  = "H"
    C  = "C"

    @property
    def rank(self) -> int:
        """Strength ordering. Higher = stronger claim."""
        return {"A": 6, "G": 5, "G*": 4, "M": 3, "H": 2, "C": 1}[self.value]

    def may_claim(self, other: ClaimClass) -> bool:
        """Can a result at `self` ceiling legitimately carry claim `other`?"""
        return other.rank <= self.rank


class SymmetryClass(str, Enum):
    """Geometry symmetry classification."""
    Td_REGULAR    = "Td_regular"     # Ideal regular tetrahedron — full theorem set
    Td_APPROX     = "Td_approximate" # Machined, <1% tolerance
    IRREGULAR     = "irregular"       # Unequal edges
    DEGENERATE    = "degenerate"      # Planar / collapsed
    MULTI_CELL    = "multi_cell"      # Array of K4 cells
    BUNDLE        = "bundle"          # Racetrack / bundled edges

    @property
    def claim_ceiling(self) -> ClaimClass:
        """Maximum claim class achievable for this symmetry."""
        ceilings = {
            "Td_regular":    ClaimClass.G,
            "Td_approximate": ClaimClass.G,  # with error bounds
            "irregular":      ClaimClass.M,
            "degenerate":     ClaimClass.M,
            "multi_cell":     ClaimClass.M,
            "bundle":         ClaimClass.M,
        }
        return ceilings[self.value]


class FrequencyRegime(str, Enum):
    """Operating frequency regime."""
    DC         = "DC"
    RESISTIVE  = "resistive"    # R >> ωL
    INDUCTIVE  = "inductive"    # ωL >> R
    FULL_WAVE  = "full_wave"    # retarded kernel needed
    INVALID    = "invalid"      # above quasi-static ceiling


class RegressionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ConfigID(str, Enum):
    """Hardware configuration."""
    A = "A"  # 6 independent coils, B-only
    B = "B"  # Connected network
    C = "C"  # Connected + vertex sources
    D = "D"  # Separate coils + electrodes (best E/B independence)
    E = "E"  # Connected + electrodes

    @property
    def has_e_channel(self) -> bool:
        return self in (ConfigID.C, ConfigID.D, ConfigID.E)


# ═══════════════════════════════════════════════════════════════════
# FIELD CONTEXT — the bridge between frozen core and exploration
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FieldContext:
    """
    Everything the exploration engine needs from the frozen field engine.
    Built once per geometry by context.build_context(). Not user-facing.

    This is the clean interface between Layer B (field engine) and
    Layer C (exploration). The solver never calls field_engine directly —
    it works through this object.
    """
    # Geometry
    V: np.ndarray               # (4, 3) vertex coordinates, meters
    L: float                    # edge length, meters

    # Field matrices (precomputed at centroid)
    F0: np.ndarray              # (3, 6) field matrix at centroid
    F0M: np.ndarray             # (3, 3) = F0 @ M — cycle field at centroid
    F0M_inv: np.ndarray         # (3, 3) = inv(F0M) — centroid inversion matrix
    F0G: np.ndarray             # (3, 3) = F0 @ G — should be ≈ 0 for Td

    # E-field
    E_vol: np.ndarray           # (3, 3) E-field volume matrix (barycentric)

    # Frozen basis (integer, from truth_kernel)
    M: np.ndarray               # (6, 3) int64 cycle basis
    G: np.ndarray               # (6, 3) int64 cut basis

    # Callable field evaluator for arbitrary points
    field_matrix_at: Callable   # r: (3,) → F: (3, 6)

    # Quality metrics (computed at construction)
    F0G_residual: float         # max|F0 @ G|, should be < 1e-12 for Td
    F0M_condition: float        # κ(F0M), should be 2.0 for regular
    claim_ceiling: ClaimClass   # determined by geometry quality

    # Inductance (optional — needed for AC)
    L_matrix: Optional[np.ndarray] = None   # (6, 6) mutual inductance
    Z_func: Optional[Callable] = None       # freq → Z(6, 6) impedance


# ═══════════════════════════════════════════════════════════════════
# CONTROL SPEC — user intention
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProbeTarget:
    """A secondary B-field target at a specific point."""
    position: Tuple[float, float, float]    # meters
    B_target: Tuple[float, float, float]    # Tesla
    priority: str = "MEDIUM"                # HARD / HIGH / MEDIUM / SOFT


@dataclass(frozen=True)
class TrajectorySpec:
    """Time-domain trajectory specification."""
    path_type: str          # "ring" | "line" | "spiral" | "custom"
    frequency: float        # Hz
    n_points: int = 36      # samples per cycle
    amplitude: float = 1.0  # relative
    # For custom paths, provide a function or array externally


@dataclass(frozen=True)
class ControlSpec:
    """
    What the user wants. Immutable after construction.
    Entry point to the pipeline.
    """
    # Primary targets (HARD constraints)
    B_target: Optional[Tuple[float, float, float]] = None   # Tesla, at centroid
    E_target: Optional[Tuple[float, float, float]] = None   # V/m, interior

    # Spatial features (HIGH priority)
    null_point: Optional[Tuple[float, float, float]] = None  # meters
    probe_targets: Tuple[ProbeTarget, ...] = ()

    # Soft preferences
    minimize_current: bool = True
    gradient_preference: Optional[Tuple[float, float, float]] = None

    # Limits
    I_max_per_edge: float = 10.0    # Amps
    V_max_per_vertex: float = 100.0 # Volts

    # Mode
    frequency: float = 0.0          # Hz, 0 = DC
    config_id: ConfigID = ConfigID.D
    trajectory: Optional[TrajectorySpec] = None

    def __post_init__(self):
        if self.B_target is None and self.E_target is None and self.null_point is None:
            raise ValueError("ControlSpec must specify at least one of B_target, E_target, null_point")


# ═══════════════════════════════════════════════════════════════════
# GEOMETRY SPEC — physical realization
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GeometrySpec:
    """
    Describes the physical realization. Input to the geometry adapter.
    The adapter validates this and produces a FieldContext.
    """
    vertices: np.ndarray                    # (4, 3) float64, meters
    edge_length: float                      # meters
    symmetry_class: SymmetryClass
    wire_radius: float = 0.0               # meters, 0 = filament
    config_id: ConfigID = ConfigID.D
    calibrated_F0: Optional[np.ndarray] = None  # (3, 6) if measured

    # Deviation report (filled by adapter)
    symmetry_deviations: Dict[str, float] = field(default_factory=dict)
    broken_assumptions: Tuple[str, ...] = ()

    @property
    def claim_ceiling(self) -> ClaimClass:
        return self.symmetry_class.claim_ceiling

    def __hash__(self):
        return hash((self.edge_length, self.symmetry_class, self.wire_radius))

    def __eq__(self, other):
        if not isinstance(other, GeometrySpec):
            return False
        return (np.allclose(self.vertices, other.vertices)
                and self.symmetry_class == other.symmetry_class)


# ═══════════════════════════════════════════════════════════════════
# DRIVE SPEC — physical drive signals (output of solver)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DriveSpec:
    """
    Physical drive specification. Output of the solver.

    CHANNEL RELATIONSHIP (important for future contributors):
        w (cycle weights) and u_coil (cut weights) are Hodge coordinates
        in edge-current space. They are ALWAYS independent — the Hodge
        decomposition guarantees M^T @ G = 0.

        u_vertex (vertex potentials) drives the E-field channel and is
        INDEPENDENT of w and u_coil in Config D hardware (separate
        electrodes). In Configs C/E where coils and electrodes share
        hardware, there may be practical coupling — but the algebraic
        channels remain orthogonal.

        I_edge = M @ w + G @ u_coil is an INVARIANT, verified at construction.
        u_vertex does NOT appear in I_edge — it drives a separate physical channel.
    """
    # Hodge coordinates (the control language)
    w: np.ndarray              # (3,) cycle weights, Amps
    u_coil: np.ndarray         # (3,) cut-coil weights, Amps
    u_vertex: np.ndarray       # (3,) vertex potentials, Volts (V0=0 gauge)

    # Physical realization (derived from Hodge coords)
    I_edge: np.ndarray         # (6,) edge currents, Amps = M @ w + G @ u_coil
    V_drive: Optional[np.ndarray] = None  # (6,) drive voltages (may be complex for AC)

    # Power budget
    P_dissipated: float = 0.0  # Watts
    P_reactive: float = 0.0    # VA
    I_max: float = 0.0         # max |I| across edges
    V_max: float = 0.0         # max |V| across edges

    # Frequency (0 = DC)
    frequency: float = 0.0
    regime: FrequencyRegime = FrequencyRegime.DC

    def verify_decomposition(self, M: np.ndarray, G: np.ndarray, tol: float = 1e-12) -> bool:
        """Verify the invariant: I_edge == M @ w + G @ u_coil."""
        I_reconstructed = M.astype(float) @ self.w + G.astype(float) @ self.u_coil
        return np.allclose(self.I_edge, I_reconstructed, atol=tol)


# ═══════════════════════════════════════════════════════════════════
# OBSERVABLE BUNDLE — evaluated field quantities
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ObservableBundle:
    """
    Field observables at a specific point or viewport.
    Produced by the observables module. Consumed by artifacts and viz.
    """
    position: np.ndarray            # (3,) meters
    viewport_id: Optional[str]      # "VP-01" through "VP-09", or None

    B_total: np.ndarray             # (3,) Tesla
    B_cycle: np.ndarray             # (3,) cycle-channel contribution
    B_cut: np.ndarray               # (3,) cut-channel contribution
    B_magnitude: float              # |B_total|

    E: Optional[np.ndarray]         # (3,) V/m, None if outside tetrahedron

    selectivity: float              # |B_cycle| / |B_cut|, inf if cut=0

    claim_class: ClaimClass
    model_notes: str = ""


# ═══════════════════════════════════════════════════════════════════
# CLAIM RECORD — provenance passport
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ClaimRecord:
    """
    Provenance. Immutable after construction. Attached to every result.
    This is the passport through customs between layers.
    """
    claim_class: ClaimClass
    assumptions: Tuple[str, ...]
    regime: FrequencyRegime

    frozen_version: str             # must match k4_frozen.__version__
    code_digest: str                # SHA-256 of computation source

    numerical_tolerances: Dict[str, float]  # e.g. {"F0G_residual": 1e-14}
    gate_status: Dict[str, bool]    # SymPy gate outcomes at runtime

    timestamp: str                  # ISO 8601

    def __post_init__(self):
        # If claiming [A] or [G], all gates must pass
        if self.claim_class in (ClaimClass.A, ClaimClass.G):
            failed = [k for k, v in self.gate_status.items() if not v]
            if failed:
                raise ValueError(
                    f"Claim [{self.claim_class.value}] requires all gates PASS. "
                    f"Failed: {failed}"
                )


# ═══════════════════════════════════════════════════════════════════
# EXPERIMENT SPEC + RESULT — structured runs
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExperimentSpec:
    """What an experiment asks for. Immutable."""
    name: str
    description: str

    control_spec: ControlSpec
    geometry_spec: GeometrySpec

    parameter_grid: Dict[str, Any]          # param_name → values to scan
    observables: Tuple[str, ...]            # e.g. ("B_centroid", "selectivity")
    viewports: Tuple[str, ...]              # "VP-01" through "VP-09"

    claim_ceiling: ClaimClass
    assumptions: Dict[str, Any]             # for preflight


@dataclass
class ExperimentResult:
    """What an experiment produces. A lab notebook entry."""
    spec: ExperimentSpec
    claim_record: ClaimRecord

    results: List[Dict[str, Any]]           # per-grid-point

    regression_status: RegressionStatus
    sympy_gate_results: Dict[str, bool]

    tier_achieved: int                      # 1, 2, or 3
    margin: float                           # σ_min / σ_max
    constraint_residuals: List[float]

    figures: Dict[str, str]                 # name → filepath
    figure_provenance: Dict[str, ClaimRecord]

    wall_time_seconds: float
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# RUN ARTIFACT — the complete serializable bundle
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RunArtifact:
    """Everything needed to reproduce and understand a run."""
    run_id: str                             # UUID
    name: str
    description: str

    control_spec: ControlSpec
    geometry_spec: GeometrySpec

    drive: DriveSpec
    observables: List[ObservableBundle]
    experiment_result: Optional[ExperimentResult] = None

    claim_record: Optional[ClaimRecord] = None

    notes: str = ""
    ledger_entries: List[str] = field(default_factory=list)
