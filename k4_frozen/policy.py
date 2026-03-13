"""
policy.py — Claim Enforcement & Drift Prevention
=================================================

THE HARD INTERFACE RULES.

This module implements the "meta-missing" contracts that GPT identified:

1. CLAIM TIER ESCALATION: Results cannot be tagged at a higher claim
   class than their weakest dependency permits. A [G] result computed
   with a midpoint Biot-Savart model auto-downgrades to [M].

2. CONFIGID CONTRACTS: Any geometry artifact claiming cycle/cut control
   must declare a ConfigID and must state whether it realizes vertex
   connectivity and KCL. No exceptions.

3. GEOMETRY CERTIFICATION: Non-ideal geometries (bundles, hypertoroids,
   planar arrays) must explicitly map their physical structure to K₄
   topology before claiming any K₄ selection rules apply.

These are NOT optional guidelines. They are executable gatekeepers.
A result that fails policy cannot be added to a SessionBundle.

Frozen at: K4 Definitive Reference v1.2.0 + GPT audit recommendations
"""

from typing import List, Optional, Tuple
from enum import Enum
from .session_schema import (
    SessionResult, ConfigID, BModelTier, EModelTier,
    ClaimClass, ObservationClass, PassFail
)


# ═══════════════════════════════════════════════════════════════════
# RULE 1: CLAIM TIER ESCALATION
# ═══════════════════════════════════════════════════════════════════
#
# The ceiling for a claim class is set by the weakest link in its
# dependency chain. This table encodes the maximum allowed claim
# class for each combination of B-model tier and observation class.
#
# Key insight: [A] requires NO model at all. [G] requires the exact
# centroid + regular-tet + finite-segment Biot-Savart. Anything else
# forces [M] or lower.

# Maximum claim class achievable given (b_model_tier, observation_class)
_CLAIM_CEILING = {
    # (b_model, obs_class) → max allowed claim class
    (BModelTier.NONE, ObservationClass.CENTROID): ClaimClass.A,
    (BModelTier.NONE, ObservationClass.FACE_CENTER): ClaimClass.A,
    (BModelTier.NONE, ObservationClass.EDGE_MIDPOINT): ClaimClass.A,
    (BModelTier.NONE, ObservationClass.VERTEX_APPROACH): ClaimClass.A,
    (BModelTier.NONE, ObservationClass.INTERIOR): ClaimClass.A,
    (BModelTier.NONE, ObservationClass.CUSTOM): ClaimClass.A,

    (BModelTier.SYMBOLIC_CENTROID, ObservationClass.CENTROID): ClaimClass.G,
    (BModelTier.SYMBOLIC_CENTROID, ObservationClass.FACE_CENTER): ClaimClass.M,
    (BModelTier.SYMBOLIC_CENTROID, ObservationClass.EDGE_MIDPOINT): ClaimClass.M,

    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.CENTROID): ClaimClass.G,
    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.FACE_CENTER): ClaimClass.M,
    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.EDGE_MIDPOINT): ClaimClass.M,
    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.VERTEX_APPROACH): ClaimClass.M,
    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.INTERIOR): ClaimClass.M,
    (BModelTier.FINITE_SEGMENT_BIOT_SAVART, ObservationClass.CUSTOM): ClaimClass.M,

    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.CENTROID): ClaimClass.M,
    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.FACE_CENTER): ClaimClass.M,
    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.EDGE_MIDPOINT): ClaimClass.M,
    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.VERTEX_APPROACH): ClaimClass.M,
    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.INTERIOR): ClaimClass.M,
    (BModelTier.MIDPOINT_BIOT_SAVART, ObservationClass.CUSTOM): ClaimClass.M,
}

# Claim class ordering for comparison
_CLAIM_RANK = {
    ClaimClass.A: 4,  # highest: pure algebra
    ClaimClass.G: 3,  # geometric exact
    ClaimClass.M: 2,  # model-dependent
    ClaimClass.H: 1,  # hardware-dependent
    ClaimClass.C: 0,  # conjecture (lowest)
}


def claim_ceiling(b_model: BModelTier, e_model: EModelTier,
                  obs_class: ObservationClass) -> ClaimClass:
    """
    Compute the maximum allowed claim class for a given model/observation
    combination.

    This is the ESCALATION RULE: you cannot tag higher than this returns.
    """
    key = (b_model, obs_class)
    b_ceiling = _CLAIM_CEILING.get(key, ClaimClass.M)

    # E-model further constrains: Level 2 surrogate forces [M] for E results
    if e_model == EModelTier.LEVEL2_POINT_ELECTRODE:
        e_ceiling = ClaimClass.M
    elif e_model == EModelTier.LEVEL1_DISCRETE_PROXY:
        e_ceiling = ClaimClass.A  # discrete gradient is pure topology
    elif e_model == EModelTier.NONE:
        e_ceiling = ClaimClass.A  # no E claim at all
    else:
        e_ceiling = ClaimClass.M

    # Return the LOWER of the two ceilings
    if _CLAIM_RANK[b_ceiling] <= _CLAIM_RANK[e_ceiling]:
        return b_ceiling
    return e_ceiling


def enforce_claim_ceiling(result: SessionResult) -> Tuple[bool, Optional[str], Optional[ClaimClass]]:
    """
    Check if a result's claim class exceeds its ceiling.

    Returns:
      (passed, violation_message, corrected_class)
      If passed is True, the claim is valid. Otherwise violation_message
      explains why and corrected_class gives the auto-downgrade.
    """
    ceiling = claim_ceiling(result.b_model_tier, result.e_model_tier,
                            result.observation_class)
    if _CLAIM_RANK[result.claim_class] > _CLAIM_RANK[ceiling]:
        msg = (
            f"Claim [{result.claim_class.value}] exceeds ceiling "
            f"[{ceiling.value}] for B-model={result.b_model_tier.value}, "
            f"E-model={result.e_model_tier.value}, "
            f"obs={result.observation_class.value}. "
            f"Auto-downgrading to [{ceiling.value}]."
        )
        return False, msg, ceiling
    return True, None, None


# ═══════════════════════════════════════════════════════════════════
# RULE 2: CONFIGID CONTRACTS
# ═══════════════════════════════════════════════════════════════════
#
# Any result making controllability claims MUST declare:
#   - Which ConfigID it assumes
#   - Whether that config supports the claimed capability
#
# The schema already has ConfigID properties (cut_realizable,
# eb_independent, has_e_channel, kcl_at_vertices). This rule
# makes them into hard gates.

def enforce_config_contract(result: SessionResult) -> List[str]:
    """
    Verify that the result's claims are consistent with its declared ConfigID.

    Returns list of violations (empty = all clear).
    """
    violations = []
    cfg = result.config_id
    qname = result.quantity_name.lower()
    notes = result.notes.lower()

    # Rule 2a: Cut-related claims need cut-realizable config
    if ("cut" in qname and "realiz" in notes) or ("cut_authority" in qname):
        if not cfg.cut_realizable:
            violations.append(
                f"Cut realizability claimed in Config {cfg.value}, "
                f"which does not support steady cut conduction. "
                f"Config B enforces KCL → cut currents cannot be sustained."
            )

    # Rule 2b: E-field claims need E-channel config
    if result.e_model_tier != EModelTier.NONE:
        if not cfg.has_e_channel:
            violations.append(
                f"E-field model specified ({result.e_model_tier.value}) "
                f"but Config {cfg.value} has no E channel. "
                f"E-channel requires Config D or E."
            )

    # Rule 2c: E/B independence claims need Config D
    if "eb_independent" in qname or "e_perp_b" in qname:
        if not cfg.eb_independent:
            violations.append(
                f"E/B independence claimed but Config {cfg.value} does not "
                f"guarantee structural E/B separation. Only Config D does."
            )

    # Rule 2d: Joint E/B views need Config D
    if result.viewport_id.value.startswith("joint_"):
        if not cfg.eb_independent:
            violations.append(
                f"Joint E/B viewport {result.viewport_id.value} used with "
                f"Config {cfg.value}. Joint views require Config D "
                f"for independent E/B channels."
            )

    return violations


# ═══════════════════════════════════════════════════════════════════
# RULE 3: GEOMETRY CERTIFICATION
# ═══════════════════════════════════════════════════════════════════
#
# Non-ideal geometries must explicitly declare their K₄ mapping.
# This is the "docking port" contract — see integration.py for the
# full spec, but here we enforce the minimum requirements.

class GeometryCertification:
    """
    Certificate that a physical geometry maps to K₄ topology.

    Any geometry artifact claiming cycle/cut control must provide one.
    """
    def __init__(self,
                 name: str,
                 description: str,
                 vertex_count: int,
                 edge_count: int,
                 is_complete_graph: bool,
                 vertex_connectivity_realized: bool,
                 kcl_enforced: bool,
                 config_id: ConfigID,
                 geometry_type: str = "regular_K4",
                 deviations: Optional[List[str]] = None,
                 calibration_required: bool = False):
        self.name = name
        self.description = description
        self.vertex_count = vertex_count
        self.edge_count = edge_count
        self.is_complete_graph = is_complete_graph
        self.vertex_connectivity_realized = vertex_connectivity_realized
        self.kcl_enforced = kcl_enforced
        self.config_id = config_id
        self.geometry_type = geometry_type
        self.deviations = deviations or []
        self.calibration_required = calibration_required

    def validate(self) -> List[str]:
        """Check that the certification is internally consistent."""
        violations = []

        # Must have 4 vertices and 6 edges to be K₄
        if self.vertex_count != 4:
            violations.append(
                f"K₄ requires exactly 4 vertices, got {self.vertex_count}. "
                f"For multi-cell systems, each cell must be certified separately."
            )
        if self.edge_count != 6:
            violations.append(
                f"K₄ requires exactly 6 edges, got {self.edge_count}. "
                f"Missing edges break the Hodge decomposition."
            )
        if not self.is_complete_graph:
            violations.append(
                "Graph is not complete. The cycle/cut decomposition ℝ⁶ = ker(D) ⊕ im(D_red^T) "
                "requires K₄. Subgraphs have different decompositions."
            )

        # KCL enforcement constrains ConfigID
        if self.kcl_enforced and not self.config_id.kcl_at_vertices:
            violations.append(
                f"KCL is enforced but Config {self.config_id.value} "
                f"does not model KCL constraints."
            )
        if not self.kcl_enforced and self.config_id.kcl_at_vertices:
            violations.append(
                f"KCL is NOT enforced but Config {self.config_id.value} "
                f"assumes KCL at vertices."
            )

        # Non-regular geometries force calibration
        if self.geometry_type != "regular_K4" and not self.calibration_required:
            violations.append(
                f"Geometry type '{self.geometry_type}' is not regular K₄. "
                f"Calibration must be flagged as required — Layer 4 theorems "
                f"(F₀·G = 0, κ = 2) do NOT hold for irregular tetrahedra."
            )

        # Deviations force claim class ceiling to [M]
        if self.deviations:
            violations.append(
                f"Deviations declared: {self.deviations}. "
                f"All results from this geometry must be tagged [M] or lower."
            )

        return violations

    def max_claim_class(self) -> ClaimClass:
        """The highest claim class any result from this geometry can carry."""
        if self.geometry_type == "regular_K4" and not self.deviations:
            return ClaimClass.G
        elif self.is_complete_graph and self.vertex_count == 4:
            return ClaimClass.M  # irregular K₄ — topology holds, EM doesn't
        else:
            return ClaimClass.H  # not even K₄ topology


# Canonical certification for the ideal case
CANONICAL_K4 = GeometryCertification(
    name="Regular K₄ (canonical)",
    description="Ideal regular tetrahedron, centroid at origin, L = 0.1m",
    vertex_count=4,
    edge_count=6,
    is_complete_graph=True,
    vertex_connectivity_realized=True,
    kcl_enforced=False,  # Config D: independent coils
    config_id=ConfigID.D,
    geometry_type="regular_K4",
)


# ═══════════════════════════════════════════════════════════════════
# COMBINED POLICY GATE
# ═══════════════════════════════════════════════════════════════════

class PolicyViolation:
    """One policy violation with severity and auto-fix."""
    def __init__(self, rule: str, message: str,
                 severity: str = "ERROR",
                 auto_fix: Optional[str] = None):
        self.rule = rule
        self.message = message
        self.severity = severity  # ERROR, WARNING, INFO
        self.auto_fix = auto_fix

    def __repr__(self):
        return f"[{self.severity}] {self.rule}: {self.message}"


def enforce_all(result: SessionResult,
                geometry: Optional[GeometryCertification] = None,
                auto_fix: bool = False) -> Tuple[List[PolicyViolation], SessionResult]:
    """
    Run ALL policy checks on a result.

    If auto_fix is True, downgrades claim classes and adds notes
    rather than rejecting. Returns the (possibly modified) result.

    Returns: (violations, result)
    """
    violations = []

    # Rule 1: Claim ceiling
    passed, msg, corrected = enforce_claim_ceiling(result)
    if not passed:
        v = PolicyViolation("CLAIM_CEILING", msg, "ERROR",
                            f"Downgrade to [{corrected.value}]")
        violations.append(v)
        if auto_fix:
            result.claim_class = corrected
            result.notes += f" [POLICY: auto-downgraded from escalation rule]"

    # Rule 2: Config contract
    config_violations = enforce_config_contract(result)
    for msg in config_violations:
        violations.append(PolicyViolation("CONFIG_CONTRACT", msg, "ERROR"))

    # Rule 3: Geometry certification
    if geometry is not None:
        geo_violations = geometry.validate()
        for msg in geo_violations:
            violations.append(PolicyViolation("GEOMETRY_CERT", msg, "WARNING"))

        # Geometry ceiling overrides claim class
        geo_ceiling = geometry.max_claim_class()
        if _CLAIM_RANK[result.claim_class] > _CLAIM_RANK[geo_ceiling]:
            msg = (
                f"Geometry '{geometry.name}' caps claims at "
                f"[{geo_ceiling.value}], but result tagged "
                f"[{result.claim_class.value}]."
            )
            violations.append(PolicyViolation("GEOMETRY_CEILING", msg, "ERROR",
                                              f"Downgrade to [{geo_ceiling.value}]"))
            if auto_fix:
                result.claim_class = geo_ceiling
                result.notes += f" [POLICY: capped by geometry certification]"

    # Rule 2b (from schema validation — run those too)
    schema_warnings = result.validate()
    for msg in schema_warnings:
        violations.append(PolicyViolation("SCHEMA", msg, "WARNING"))

    return violations, result


def gate(result: SessionResult,
         geometry: Optional[GeometryCertification] = None) -> SessionResult:
    """
    Hard gate: enforce all policies, auto-fix what can be fixed,
    raise on hard violations.

    This is the function that should wrap every SessionBundle.add() call.
    """
    violations, result = enforce_all(result, geometry, auto_fix=True)

    errors = [v for v in violations if v.severity == "ERROR" and v.auto_fix is None]
    if errors:
        msg = "Policy violations that cannot be auto-fixed:\n"
        msg += "\n".join(f"  {v}" for v in errors)
        raise PolicyError(msg)

    # Attach violation log to notes
    warnings = [v for v in violations if v.severity in ("WARNING", "INFO")]
    if warnings:
        result.notes += " | Warnings: " + "; ".join(v.message for v in warnings[:3])

    return result


class PolicyError(Exception):
    """Raised when a result violates hard policy rules that cannot be auto-fixed."""
    pass


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("POLICY ENFORCEMENT SELF-TEST")
    print("=" * 60)

    # Test 1: Valid [G] result at centroid
    r1 = SessionResult(
        description="Cut annihilation test",
        config_id=ConfigID.D,
        b_model_tier=BModelTier.SYMBOLIC_CENTROID,
        claim_class=ClaimClass.G,
        observation_class=ObservationClass.CENTROID,
        quantity_name="F0G_norm",
    )
    v1, r1 = enforce_all(r1, CANONICAL_K4)
    errors1 = [v for v in v1 if v.severity == "ERROR"]
    print(f"  Test 1 (valid [G] at centroid): {'✓ PASS' if not errors1 else '✗ FAIL'}")

    # Test 2: [G] claim at face center with finite-segment BS → should downgrade to [M]
    r2 = SessionResult(
        description="Face center condition number",
        config_id=ConfigID.A,
        b_model_tier=BModelTier.FINITE_SEGMENT_BIOT_SAVART,
        claim_class=ClaimClass.G,  # TOO HIGH
        observation_class=ObservationClass.FACE_CENTER,
        quantity_name="cond_FM",
    )
    v2, r2 = enforce_all(r2, CANONICAL_K4, auto_fix=True)
    print(f"  Test 2 ([G] at face → auto-downgrade): "
          f"{'✓ PASS' if r2.claim_class == ClaimClass.M else '✗ FAIL'}")

    # Test 3: E-field claim on Config B (no E channel)
    r3 = SessionResult(
        description="E-field from passive network",
        config_id=ConfigID.B,
        e_model_tier=EModelTier.LEVEL2_POINT_ELECTRODE,
        claim_class=ClaimClass.M,
        quantity_name="E_interior",
    )
    v3, r3 = enforce_all(r3)
    config_errors = [v for v in v3 if v.rule == "CONFIG_CONTRACT"]
    print(f"  Test 3 (E on Config B → violation): "
          f"{'✓ PASS' if len(config_errors) > 0 else '✗ FAIL'}")

    # Test 4: Non-K₄ geometry
    bad_geo = GeometryCertification(
        name="Triangle array",
        description="3-vertex planar structure",
        vertex_count=3, edge_count=3,
        is_complete_graph=True,
        vertex_connectivity_realized=True,
        kcl_enforced=False,
        config_id=ConfigID.A,
        geometry_type="planar_K3",
    )
    geo_violations = bad_geo.validate()
    print(f"  Test 4 (K₃ geometry → violation): "
          f"{'✓ PASS' if len(geo_violations) > 0 else '✗ FAIL'}")

    # Test 5: Irregular K₄ without calibration flag
    irregular = GeometryCertification(
        name="Squashed tetrahedron",
        description="Non-regular K₄ with unequal edges",
        vertex_count=4, edge_count=6,
        is_complete_graph=True,
        vertex_connectivity_realized=True,
        kcl_enforced=False,
        config_id=ConfigID.D,
        geometry_type="irregular_K4",
        calibration_required=False,  # WRONG — must be True
    )
    irr_violations = irregular.validate()
    print(f"  Test 5 (irregular K₄ no calibration → violation): "
          f"{'✓ PASS' if len(irr_violations) > 0 else '✗ FAIL'}")

    # Test 6: Canonical K₄ validates clean
    can_violations = CANONICAL_K4.validate()
    print(f"  Test 6 (canonical K₄ validates clean): "
          f"{'✓ PASS' if len(can_violations) == 0 else '✗ FAIL'}")

    print()
    print("  All policy tests complete.")
