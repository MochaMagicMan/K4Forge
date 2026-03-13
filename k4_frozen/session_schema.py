"""
session_schema.py — Session Schema & Claim Taxonomy
====================================================

Every computational artifact (plot, table, numerical result) produced
in any K4 session is expressible as a SessionResult record.

Mirrors K4_DISCRETE_MAP_v3.md exactly:
  - Config IDs from Part II
  - Model tiers from Part III
  - Claim classes from the taxonomy
  - View IDs from Part X
  - Normalization conventions from Part VII

Frozen at: K4 Definitive Reference v1.2.0 / Discrete Map v3
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json


# ═══════════════════════════════════════════════════════════════════
# ENUMERATIONS (from v3 ontology)
# ═══════════════════════════════════════════════════════════════════

class ConfigID(str, Enum):
    """Hardware configurations from Part II."""
    A = "A"   # Independent coil loops
    B = "B"   # Passive connected network
    C = "C"   # Connected + vertex current sources
    D = "D"   # Separate coils + isolated vertex electrodes
    E = "E"   # Connected + vertex electrodes (hybrid)

    @property
    def homogeneous_kcl(self) -> bool:
        """D·I = 0 strictly: no current enters or leaves any vertex externally.
        Only Config B (passive closed network) satisfies this.
        Cut-space modes are impossible in this configuration."""
        return self == ConfigID.B

    @property
    def driven_kcl(self) -> bool:
        """D·I = J_inject: vertex divergence equals externally injected current.
        Configs C and E allow vertex current injection from external sources.
        KCL is satisfied globally (including the injection), not locally at vertices."""
        return self in (ConfigID.C, ConfigID.E)

    @property
    def kcl_at_vertices(self) -> bool:
        """Legacy: True if the network topology connects at vertices.
        For precise semantics, use homogeneous_kcl or driven_kcl."""
        return self.homogeneous_kcl or self.driven_kcl

    @property
    def cut_realizable(self) -> bool:
        return self in (ConfigID.A, ConfigID.C, ConfigID.D, ConfigID.E)

    @property
    def eb_independent(self) -> bool:
        return self == ConfigID.D

    @property
    def has_e_channel(self) -> bool:
        return self in (ConfigID.D, ConfigID.E)


class BModelTier(str, Enum):
    FINITE_SEGMENT_BIOT_SAVART = "finite_segment_biot_savart"
    MIDPOINT_BIOT_SAVART = "midpoint_biot_savart"
    SYMBOLIC_CENTROID = "symbolic_centroid"
    NONE = "none"


class EModelTier(str, Enum):
    LEVEL1_DISCRETE_PROXY = "level1_discrete_proxy"
    LEVEL2_POINT_ELECTRODE = "level2_point_electrode"
    LEVEL3_QUASISTATIC = "level3_quasistatic"
    NONE = "none"


class ClaimClass(str, Enum):
    """Claim taxonomy from v3."""
    A = "A"   # Algebraic exact
    G = "G"   # Geometric exact
    M = "M"   # Model-dependent numerical
    H = "H"   # Hardware-dependent
    C = "C"   # Conjecture / open

    @property
    def is_exact(self) -> bool:
        return self in (ClaimClass.A, ClaimClass.G)


class ObservationClass(str, Enum):
    CENTROID = "T"
    FACE_CENTER = "F"
    EDGE_MIDPOINT = "E"
    VERTEX_APPROACH = "V"
    INTERIOR = "interior"
    CUSTOM = "custom"


class ViewportID(str, Enum):
    B_CENTROID_SLICE_XY = "B_centroid_slice_xy"
    B_CENTROID_SLICE_YZ = "B_centroid_slice_yz"
    B_CENTROID_SLICE_XZ = "B_centroid_slice_xz"
    B_ORBIT_OVERLAY = "B_orbit_overlay"
    B_RADIAL_C3 = "B_radial_c3"
    B_RADIAL_C2 = "B_radial_c2"
    B_NULL_GLYPHS = "B_null_glyphs"
    E_CENTROID_SLICE_XY = "E_centroid_slice_xy"
    E_CENTROID_SLICE_YZ = "E_centroid_slice_yz"
    E_CENTROID_SLICE_XZ = "E_centroid_slice_xz"
    E_EQUIPOTENTIAL = "E_equipotential"
    JOINT_EDOTB = "joint_EdotB"
    JOINT_ECROSSB = "joint_ExB"
    JOINT_ANGLE = "joint_angle_EB"
    JOINT_TRACES = "joint_traces"
    TABLE_SKELETON = "table_skeleton_atlas"
    TABLE_INVERSE = "table_inverse_problem"
    TABLE_NULL = "table_null_directions"
    CUSTOM = "custom"


class Normalization(str, Enum):
    SI_PHYSICAL = "SI_physical"
    DIMENSIONLESS_RATIO = "dimensionless"
    NORMALIZED_UNIT = "normalized_unit"
    CUSTOM = "custom"


class PassFail(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NOT_EVALUATED = "not_eval"


class Provenance(str, Enum):
    PROVEN = "PROVEN"
    ANALYTIC = "ANALYTIC"
    NUMERICAL = "NUMERICAL"
    STRUCTURAL = "STRUCTURAL"
    DERIVED = "DERIVED"


# ═══════════════════════════════════════════════════════════════════
# RESULT RECORD
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SessionResult:
    """One computational artifact from a K4 session."""
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str = ""

    config_id: ConfigID = ConfigID.D
    b_model_tier: BModelTier = BModelTier.FINITE_SEGMENT_BIOT_SAVART
    e_model_tier: EModelTier = EModelTier.NONE
    claim_class: ClaimClass = ClaimClass.M

    observation_class: ObservationClass = ObservationClass.CENTROID
    observation_point: Optional[str] = None
    observation_coords: Optional[List[float]] = None

    viewport_id: ViewportID = ViewportID.CUSTOM
    quantity_name: str = ""
    normalization: Normalization = Normalization.SI_PHYSICAL

    value: Optional[float] = None
    vector_value: Optional[List[float]] = None
    matrix_value: Optional[List[List[float]]] = None
    singular_values: Optional[List[float]] = None
    condition_number: Optional[float] = None
    rank: Optional[int] = None

    residual: Optional[float] = None
    residual_relative: Optional[float] = None
    status: PassFail = PassFail.NOT_EVALUATED

    theorem_ids: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> List[str]:
        """Check consistency with v3 ontology."""
        warnings = []

        # Joint E/B views need Config D
        if self.viewport_id in (ViewportID.JOINT_EDOTB, ViewportID.JOINT_ECROSSB,
                                ViewportID.JOINT_ANGLE, ViewportID.JOINT_TRACES):
            if not self.config_id.eb_independent:
                warnings.append(
                    f"Joint E/B view with Config {self.config_id.value} (E/B coupled)")

        # E views need E model
        if self.viewport_id.value.startswith("E_") or self.viewport_id.value.startswith("joint_"):
            if self.e_model_tier == EModelTier.NONE:
                warnings.append(f"E-field view with no E-model specified")

        # Exact claims at non-centroid need justification
        if self.claim_class.is_exact:
            if self.b_model_tier not in (BModelTier.SYMBOLIC_CENTROID, BModelTier.NONE):
                if self.observation_class != ObservationClass.CENTROID:
                    warnings.append(f"[{self.claim_class.value}] at non-centroid with numerical B-model")

        # Centroid κ = 2 is [G], not [M]
        if (self.observation_class == ObservationClass.CENTROID and
            self.quantity_name in ("cond_FM", "cond_FE_red") and
            self.claim_class == ClaimClass.M):
            warnings.append(f"Centroid {self.quantity_name} is [G] (P13), tagged as [M]")

        return warnings

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if isinstance(v, Enum):
                d[k] = v.value
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], Enum):
                d[k] = [x.value for x in v]
            else:
                d[k] = v
        return d


# ═══════════════════════════════════════════════════════════════════
# SESSION BUNDLE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SessionBundle:
    """A collection of results from one session."""
    session_id: str
    session_date: str
    description: str
    regime_declaration: str = (
        "All controllability claims are configuration- and model-specific. "
        "Algebraic decompositions (Layer 1) are exact statements about "
        "edge-coordinate spaces and do not by themselves imply physical "
        "actuation authority."
    )
    results: List[SessionResult] = field(default_factory=list)
    _policy_enforced: bool = True  # Set False ONLY for legacy/testing

    def add(self, result: SessionResult,
            geometry: Optional['GeometryCertification'] = None,
            skip_policy: bool = False) -> List[str]:
        """
        Add a result to the session.
        
        POLICY ENFORCEMENT: By default, every result passes through
        policy.gate() before acceptance. This auto-downgrades claim
        classes that exceed their ceiling and catches config violations.
        
        Set skip_policy=True ONLY for testing or legacy import.
        Results added without policy get '[UNGATED]' in their notes.
        """
        result.session_id = self.session_id
        warnings = result.validate()
        
        if self._policy_enforced and not skip_policy:
            try:
                from .policy import gate as policy_gate
                result = policy_gate(result, geometry=geometry)
            except ImportError:
                pass  # policy module not available (minimal install)
            except Exception as e:
                warnings.append(f"Policy gate error: {e}")
        elif skip_policy:
            result.notes += " [UNGATED — policy skipped]"
        
        self.results.append(result)
        return warnings

    def filter_by_claim(self, cls: ClaimClass) -> List[SessionResult]:
        return [r for r in self.results if r.claim_class == cls]

    def exact_results(self) -> List[SessionResult]:
        return [r for r in self.results if r.claim_class.is_exact]

    def summary(self) -> str:
        lines = [
            f"Session: {self.session_id} ({self.session_date})",
            f"Description: {self.description}",
            f"Total results: {len(self.results)}",
        ]
        for c in ClaimClass:
            n = len(self.filter_by_claim(c))
            if n > 0:
                lines.append(f"  [{c.value}] {c.name}: {n}")

        warns = []
        for r in self.results:
            w = r.validate()
            if w:
                warns.extend([(r.quantity_name, m) for m in w])
        if warns:
            lines.append(f"\n  ⚠ {len(warns)} warnings:")
            for name, msg in warns[:10]:
                lines.append(f"    {name}: {msg}")
        else:
            lines.append(f"\n  ✅ All results pass validation")
        return "\n".join(lines)

    def to_json(self, path: Optional[str] = None) -> str:
        data = {
            "session_id": self.session_id,
            "session_date": self.session_date,
            "description": self.description,
            "regime_declaration": self.regime_declaration,
            "results": [r.to_dict() for r in self.results],
        }
        j = json.dumps(data, indent=2)
        if path:
            with open(path, 'w') as f:
                f.write(j)
        return j
