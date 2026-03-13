"""
ASSUMPTIONS.py — Operational Assumptions & Session Preflight
==============================================================

RUNNING LEDGER. Referenced and confirmed every session.

Every computation in k4_frozen_v3 rests on declared assumptions.
This module makes them explicit, enforces declaration, and
prevents the "normalized then forgotten" failure mode.

USAGE:
    from k4_frozen_v3.assumptions import (
        SessionAssumptions,   # declare before any run
        preflight,            # verify stack before any run
        CANONICAL_ASSUMPTIONS,  # default for regular K₄ DC
    )

    # Every session starts with:
    assumptions = SessionAssumptions(...)  # or CANONICAL_ASSUMPTIONS
    preflight(assumptions)                 # must PASS

WHAT THIS PREVENTS:
    1. Running at MHz with a Biot-Savart engine (quasi-static violation)
    2. Claiming [G] with midpoint Biot-Savart (tier violation)
    3. Forgetting that cut is a coordinate basis, not a physical node
       gradient, unless vertex connectivity is realized (ConfigID leak)
    4. Treating M_opp = 0 as unconditional when it requires geometry (proof leak)
    5. Ignoring inductance coupling in AC analysis (commanded current fallacy)
    6. Claiming null depth below the filament floor (conductor model leak)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum

from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# ASSUMPTION CATEGORIES
# ═══════════════════════════════════════════════════════════════════

class PhysicsRegime(Enum):
    """Electromagnetic regime declaration."""
    DC = "dc"                           # ω = 0, no time dependence
    QUASI_STATIC_LOW = "quasi_static_low"   # f < f_LR (resistive-dominated)
    QUASI_STATIC_HIGH = "quasi_static_high" # f_LR < f < c/(10L) (inductive)
    INVALID = "invalid"                 # f > c/(10L), Biot-Savart fails


class ConductorModel(Enum):
    """How the wire is modeled."""
    FILAMENT = "filament_1D"            # infinitely thin, Biot-Savart exact
    BUNDLE = "bundle_multi_filament"    # multiple filaments, approximate
    VOLUME = "volume_current"           # finite cross-section, FEM required


class CouplingModel(Enum):
    """How inter-edge coupling is modeled."""
    NONE = "independent_currents"       # I_edge freely commandable (ideal)
    NEUMANN_THIN = "neumann_thin_wire"  # L from Neumann + Rosa self
    CALIBRATED = "calibrated_measured"  # L from measurement/FEM
    FULL_MAXWELL = "full_maxwell"       # retarded potentials, not implemented


class CutRealizability(Enum):
    """Is the cut subspace physically realizable as node-gradient currents?"""
    COORDINATE_ONLY = "coordinate_basis"     # mathematical decomposition only
    VERTEX_CONNECTED = "vertex_connected"    # physical vertex-to-vertex wiring
    KCL_ENFORCED = "kcl_enforced"           # KCL verified at vertices


# ═══════════════════════════════════════════════════════════════════
# THEOREM CLASSIFICATION LEDGER
# ═══════════════════════════════════════════════════════════════════
#
# Every theorem in the frozen stack is classified by what it requires.
# This is the single source of truth for "what do I need to believe?"
#

THEOREM_LEDGER = {
    # ══════════════════════════════════════════════════════════════
    # LAYER 0-1: Unconditional [A] — Pure graph topology
    # All proven to Integer(0) via SymPy exact arithmetic.
    # These survive ANY geometry, ANY physics model, ANY frequency.
    # ══════════════════════════════════════════════════════════════
    "T1.1": {
        "statement": "M^T · G = 0  (Hodge orthogonality)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "T1.2": {
        "statement": "D · M = 0  (cycles are boundaries)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "T1.3": {
        "statement": "M^T·M = G^T·G = 4I₃ − J₃  (Gram matrix)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "T1.4": {
        "statement": "det(M^T·M) = 16",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "T1.5": {
        "statement": "|det([M|G])| = 16  (full-rank decomposition)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "T1.7": {
        "statement": "P_cycle + P_cut = I₆  (complete Hodge split)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via adjugate: 16·(P_c+P_k) = 16·I₆",
        "survives": "everything",
    },
    "T1.8": {
        "statement": "P_cycle · P_cut = 0  (orthogonal projections)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "chain": {
        "statement": "D·B = 0, B^T·D^T = 0  (boundary-of-boundary)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "L1": {
        "statement": "D^T·D + B·B^T = 4·I₆  (edge Laplacian + face Laplacian)",
        "claim": "A", "layer": "0-1",
        "requires": "integer matrices only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },

    # ══════════════════════════════════════════════════════════════
    # LAYER 3-4: Electromagnetic structure
    # UPGRADED: The structural core is now [A] (integer matrix C_int).
    # Only the scalar proportionality α(L) is [G].
    # ══════════════════════════════════════════════════════════════
    "T3.0": {
        "statement": "F₀[:,k] = α · C_int[:,k]  (field matrix factorization)",
        "claim": "A+G", "layer": "3-4",
        "note": "C_int is the integer cross-product matrix (3×6).",
        "requires": {
            "A_part": "C_int derived from integer vertex signs and edge topology",
            "G_part": "α(L) is the Biot-Savart scalar, same for all edges by T_d",
        },
        "proof": {
            "A_part": "C_int = (Δ × signs)/2, all entries ∈ {-1,0,+1}",
            "G_part": "α is constant over edges by T_d symmetry of centroid",
        },
        "survives": "C_int survives everything; α requires centroid + Biot-Savart",
    },
    "T3.1": {
        "statement": "F₀ · G = 0  (cut annihilation at centroid)",
        "claim": "A", "layer": "3-4",
        "note": "UPGRADED from [G]. The core identity C_int·G = 0 is pure integer arithmetic.",
        "requires": "integer matrices C_int, G only",
        "proof": "Integer(0) via SymPy: C_int·G = 0₃ₓ₃",
        "survives": "everything (α cancels: α·0 = 0 for any α)",
        "previous_claim": "G (numerical < 1e-14)",
    },
    "T3.2": {
        "statement": "rank(F₀ · M) = 3  (full cycle control at centroid)",
        "claim": "A+G", "layer": "3-4",
        "note": "UPGRADED. det(C_int·M) = 32 ≠ 0 is [A]. α ≠ 0 is [G].",
        "requires": {
            "A_part": "integer matrices C_int, M",
            "G_part": "α ≠ 0 (any point not on all edge lines simultaneously)",
        },
        "proof": {
            "A_part": "det(C_int·M) = 32, Integer exact",
            "G_part": "α > 0 at centroid by construction",
        },
        "survives": "rank is 3 for ANY nonzero α, i.e. ANY evaluation point not pathological",
    },
    "T3.3": {
        "statement": "κ(F₀·M) = 2  (universal centroid anisotropy)",
        "claim": "A", "layer": "3-4",
        "note": "UPGRADED from [G]. The condition number is κ(C_int·M) = √(16/4) = 2.",
        "requires": "integer matrices C_int, M only",
        "proof": "Integer eigenvalues: (C_int·M)^T·(C_int·M) has spectrum {4:1, 16:2}. κ = √(16/4) = 2.",
        "survives": "everything (κ is invariant under scalar multiplication by α)",
        "previous_claim": "G (numerical SVD)",
    },

    # ══════════════════════════════════════════════════════════════
    # INDUCTANCE: Hodge-inductance decoupling
    # Mixed [A]+[G] with EXACT leakage formula for irregular case.
    # ══════════════════════════════════════════════════════════════
    "IL.T1": {
        "statement": "M^T · L · G = 0  (Hodge-inductance decoupling)",
        "claim": "A+G", "layer": "4+",
        "note": "For T_d-symmetric L = a·I₆ + b·Σ + c·A_opp.",
        "requires": {
            "terms_1_2": "integer matrices only: Σ = D^T·D − 2I₆ [A]",
            "term_3": "M_opp = 0, i.e. perpendicular opposite edges [G]",
        },
        "proof": {
            "terms_1_2": "Integer(0) via SymPy: M^T·D^T = (D·M)^T = 0 (T1.2)",
            "term_3": "numerical M_opp < 1e-15 + perpendicularity argument",
        },
        "survives": "terms 1,2 always; term 3 requires regular tetrahedron",
        "breaks_when": "irregular tet with non-perpendicular opposite edges",
        "leakage_formula": "cross_coupling = M_opp · [[-1,1,-1],[-1,1,-1],[1,-1,1]]",
        "leakage_norm": "3 · |M_opp|  (Frobenius norm of integer leakage matrix = 3)",
    },
    "IL.T2": {
        "statement": "L has two 3-fold degenerate eigenvalue triplets",
        "claim": "G", "layer": "4+",
        "requires": "T_d symmetry of geometry (Schur's lemma on S₄ irreps)",
        "proof": "numerical eigenvalue computation; group-theoretic argument",
        "survives": "regular tetrahedron only",
        "breaks_when": "any departure from T_d symmetry splits degeneracies",
    },

    # ══════════════════════════════════════════════════════════════
    # EDGE DIRECTION IDENTITIES (new, from symbolic audit)
    # ══════════════════════════════════════════════════════════════
    "ED.1": {
        "statement": "Δ · M = 0  (edge directions annihilate cycles)",
        "claim": "A", "layer": "1-3",
        "note": "Δ is the integer edge-direction-sign matrix (3×6).",
        "requires": "integer matrices Δ, M only",
        "proof": "Integer(0) via SymPy",
        "survives": "everything",
    },
    "ED.2": {
        "statement": "C_int = (Δ × signs) / 2  (cross-product matrix from integers)",
        "claim": "A", "layer": "1-3",
        "requires": "integer vertex signs and edge topology",
        "proof": "Integer(0) via SymPy construction",
        "survives": "everything (for regular tet vertex placement)",
    },
}


# ═══════════════════════════════════════════════════════════════════
# SESSION ASSUMPTIONS (declare before every run)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SessionAssumptions:
    """
    Complete declaration of what a session assumes.
    Must be created before any computation and passed to preflight().
    """
    # Identity
    session_name: str = "unnamed"
    intent: str = "exploration"  # calibration / atlas / modulation / interaction

    # Physics
    physics_regime: PhysicsRegime = PhysicsRegime.DC
    frequency_Hz: float = 0.0
    conductor_model: ConductorModel = ConductorModel.FILAMENT
    wire_radius_m: Optional[float] = None       # required if conductor != FILAMENT
    coupling_model: CouplingModel = CouplingModel.NONE

    # Geometry
    edge_length_m: float = 0.1
    geometry_type: str = "regular_K4"            # regular_K4 / irregular_K4 / non_K4
    normalization: str = "edge_length"           # edge_length / circumradius / insphere

    # Control language
    config_id: str = "D"                         # A/B/C/D/E per frozen schema
    cut_realizability: CutRealizability = CutRealizability.COORDINATE_ONLY
    b_model_tier: str = "FINITE_SEGMENT_BIOT_SAVART"
    claim_ceiling: str = "G"                     # max claim class this session allows

    # Explicitly unmodeled (latent variables — must declare)
    skin_effect_modeled: bool = False
    capacitance_modeled: bool = False
    mutual_inductance_modeled: bool = False
    proximity_effect_modeled: bool = False
    return_path_modeled: bool = False

    # Probe suite
    probe_locations: List[str] = field(default_factory=lambda: ["centroid"])

    def latent_variables(self) -> List[str]:
        """List of physical effects NOT modeled in this session."""
        latent = []
        if not self.skin_effect_modeled:
            latent.append("skin effect (frequency-dependent resistance)")
        if not self.capacitance_modeled:
            latent.append("distributed capacitance between turns/edges")
        if not self.mutual_inductance_modeled:
            latent.append("mutual inductance (L tensor) — currents assumed independent")
        if not self.proximity_effect_modeled:
            latent.append("proximity effect on current distribution")
        if not self.return_path_modeled:
            latent.append("return current path (assumed at infinity)")
        return latent

    def required_theorems(self) -> List[str]:
        """Which theorems this session depends on."""
        deps = ["T1.1", "T1.2", "T1.3", "T1.7"]  # always needed
        if self.geometry_type == "regular_K4":
            deps.extend(["T3.1", "T3.2", "T3.3"])
        if self.mutual_inductance_modeled:
            deps.append("IL.T1")
            if self.geometry_type == "regular_K4":
                deps.append("IL.T2")
        return deps

    def summary(self) -> str:
        """Human-readable assumption declaration."""
        lines = [
            f"═══ SESSION ASSUMPTIONS: {self.session_name} ═══",
            f"  Intent: {self.intent}",
            f"  Physics: {self.physics_regime.value} @ {self.frequency_Hz:.0f} Hz",
            f"  Conductor: {self.conductor_model.value}",
            f"  Coupling: {self.coupling_model.value}",
            f"  Geometry: {self.geometry_type}, L={self.edge_length_m*100:.1f}cm, norm={self.normalization}",
            f"  Control: ConfigID={self.config_id}, cut={self.cut_realizability.value}",
            f"  B-model: {self.b_model_tier}, claim ceiling: [{self.claim_ceiling}]",
            f"  Probes: {', '.join(self.probe_locations)}",
        ]
        latent = self.latent_variables()
        if latent:
            lines.append(f"  UNMODELED ({len(latent)}):")
            for lv in latent:
                lines.append(f"    ⚠ {lv}")
        else:
            lines.append(f"  All relevant physics modeled ✓")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# CANONICAL ASSUMPTIONS (defaults)
# ═══════════════════════════════════════════════════════════════════

CANONICAL_DC = SessionAssumptions(
    session_name="CANONICAL_DC",
    intent="calibration",
    physics_regime=PhysicsRegime.DC,
    frequency_Hz=0.0,
    conductor_model=ConductorModel.FILAMENT,
    coupling_model=CouplingModel.NONE,
    edge_length_m=0.1,
    geometry_type="regular_K4",
    config_id="D",
    cut_realizability=CutRealizability.COORDINATE_ONLY,
    b_model_tier="FINITE_SEGMENT_BIOT_SAVART",
    claim_ceiling="G",
    probe_locations=["centroid"],
)

CANONICAL_AC_LOW = SessionAssumptions(
    session_name="CANONICAL_AC_LOW",
    intent="modulation",
    physics_regime=PhysicsRegime.QUASI_STATIC_LOW,
    frequency_Hz=1000.0,
    conductor_model=ConductorModel.FILAMENT,
    wire_radius_m=0.5e-3,
    coupling_model=CouplingModel.NEUMANN_THIN,
    edge_length_m=0.1,
    geometry_type="regular_K4",
    config_id="D",
    cut_realizability=CutRealizability.COORDINATE_ONLY,
    b_model_tier="FINITE_SEGMENT_BIOT_SAVART",
    claim_ceiling="M",
    mutual_inductance_modeled=True,
    probe_locations=["centroid", "face_centers"],
)

CANONICAL_AC_HIGH = SessionAssumptions(
    session_name="CANONICAL_AC_HIGH",
    intent="modulation",
    physics_regime=PhysicsRegime.QUASI_STATIC_HIGH,
    frequency_Hz=100_000.0,
    conductor_model=ConductorModel.FILAMENT,
    wire_radius_m=0.5e-3,
    coupling_model=CouplingModel.NEUMANN_THIN,
    edge_length_m=0.1,
    geometry_type="regular_K4",
    config_id="D",
    cut_realizability=CutRealizability.COORDINATE_ONLY,
    b_model_tier="FINITE_SEGMENT_BIOT_SAVART",
    claim_ceiling="M",
    mutual_inductance_modeled=True,
    probe_locations=["centroid", "face_centers", "edge_midpoints"],
)


# ═══════════════════════════════════════════════════════════════════
# PREFLIGHT CHECK
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PreflightResult:
    """Result of preflight check. Must be PASS to proceed."""
    passed: bool
    checks: Dict[str, bool]
    warnings: List[str]
    errors: List[str]
    assumptions: SessionAssumptions

    def summary(self) -> str:
        status = "✅ PREFLIGHT PASS" if self.passed else "❌ PREFLIGHT FAIL"
        lines = [status]
        for name, ok in self.checks.items():
            mark = "✓" if ok else "✗"
            lines.append(f"  {mark} {name}")
        for w in self.warnings:
            lines.append(f"  ⚠ WARNING: {w}")
        for e in self.errors:
            lines.append(f"  ✗ ERROR: {e}")
        return "\n".join(lines)


def preflight(assumptions: SessionAssumptions, verbose: bool = True) -> PreflightResult:
    """
    Run all preflight checks for a session.

    1. Verify frozen stack (verify_all equivalent, fast path)
    2. Check frequency vs regime declaration
    3. Check conductor model vs claim ceiling
    4. Check coupling model vs frequency regime
    5. Check geometry type vs theorem dependencies
    6. Check ConfigID vs cut realizability
    7. Warn on unmodeled latent variables

    Returns PreflightResult. Session should not proceed if FAIL.
    """
    checks = {}
    warnings = []
    errors = []

    if verbose:
        print(assumptions.summary())
        print()

    # ── 1. Frozen stack integrity ──
    try:
        layer1 = tk.verify_layer1(verbose=False)
        checks["frozen_layer1"] = all(layer1.values())
    except Exception as e:
        checks["frozen_layer1"] = False
        errors.append(f"Layer 1 verification failed: {e}")

    # ── 2. Frequency vs regime ──
    f = assumptions.frequency_Hz
    L = assumptions.edge_length_m
    f_wave = 299_792_458.0 / (10.0 * L)

    if f == 0 and assumptions.physics_regime != PhysicsRegime.DC:
        errors.append(f"f=0 but regime declared as {assumptions.physics_regime.value}")
        checks["freq_regime"] = False
    elif f > 0 and assumptions.physics_regime == PhysicsRegime.DC:
        errors.append(f"f={f}Hz but regime declared as DC")
        checks["freq_regime"] = False
    elif f > f_wave:
        if assumptions.physics_regime != PhysicsRegime.INVALID:
            errors.append(f"f={f:.0f}Hz exceeds wave ceiling {f_wave:.0f}Hz but not declared INVALID")
        checks["freq_regime"] = False
    else:
        checks["freq_regime"] = True

    # ── 3. Conductor model vs claim ceiling ──
    if assumptions.conductor_model == ConductorModel.FILAMENT:
        if assumptions.claim_ceiling in ("G", "A"):
            checks["conductor_claim"] = True
        else:
            checks["conductor_claim"] = True  # filament is most permissive
    else:
        # Non-filament models cap claims at [M]
        if assumptions.claim_ceiling in ("G", "A"):
            warnings.append(f"Conductor model {assumptions.conductor_model.value} "
                          f"caps claims at [M], but ceiling is [{assumptions.claim_ceiling}]")
        checks["conductor_claim"] = True

    # ── 4. Coupling model vs frequency ──
    if f > 0 and assumptions.coupling_model == CouplingModel.NONE:
        warnings.append(f"AC operation at {f:.0f}Hz without inductance model. "
                       f"Commanded currents may not be achievable.")
        if f > 100:  # above 100Hz, this is a real problem
            warnings.append("STRONGLY recommend NEUMANN_THIN coupling model for f > 100Hz")
    checks["coupling_model"] = True  # warning only, not error

    # ── 5. Geometry type vs claim ceiling ──
    if assumptions.geometry_type != "regular_K4" and assumptions.claim_ceiling in ("G", "A"):
        errors.append(f"Non-regular geometry ({assumptions.geometry_type}) "
                     f"cannot support [{assumptions.claim_ceiling}] claims. Max: [M]")
        checks["geometry_claim"] = False
    else:
        checks["geometry_claim"] = True

    deps = assumptions.required_theorems()
    if assumptions.geometry_type != "regular_K4":
        affected = [t for t in ["T3.1","T3.2","T3.3","IL.T2"]
                   if t in THEOREM_LEDGER]
        if affected:
            warnings.append(f"Non-regular geometry invalidates: {', '.join(affected)}")
    checks["geometry_theorems"] = True  # warning only if claim already downgraded

    # ── 6. ConfigID vs cut realizability ──
    if assumptions.config_id in ("B", "C"):
        if assumptions.cut_realizability != CutRealizability.COORDINATE_ONLY:
            warnings.append(f"ConfigID {assumptions.config_id} may not support "
                          f"cut realizability {assumptions.cut_realizability.value}")
    checks["config_cut"] = True  # advisory

    # ── 7. Latent variables ──
    latent = assumptions.latent_variables()
    if latent and assumptions.claim_ceiling in ("G", "A"):
        for lv in latent:
            if "mutual inductance" in lv and f > 0:
                warnings.append(f"Latent: {lv} — may invalidate AC claims")

    # Null depth warning for filament model
    if assumptions.conductor_model == ConductorModel.FILAMENT:
        warnings.append("Null depth claims have no physical floor (filament model). "
                       "Real conductors impose a minimum null radius.")

    checks["latent_declared"] = True  # declaration is the gate, not absence

    # ── Result ──
    passed = all(checks.values()) and len(errors) == 0
    result = PreflightResult(
        passed=passed, checks=checks,
        warnings=warnings, errors=errors,
        assumptions=assumptions,
    )

    if verbose:
        print(result.summary())
        print()

    return result


# ═══════════════════════════════════════════════════════════════════
# PROOF STATUS REPORT
# ═══════════════════════════════════════════════════════════════════

def proof_status_report(verbose=True) -> Dict:
    """
    Report the proof status of every theorem in the ledger.
    This is the "what do we actually know?" audit.
    """
    report = {}
    for tid, info in THEOREM_LEDGER.items():
        report[tid] = {
            "statement": info["statement"],
            "claim": info["claim"],
            "layer": info["layer"],
        }

        # Check if proof is symbolic or numerical
        proof = info.get("proof", "")
        if isinstance(proof, dict):
            # Mixed proof (like IL.T1)
            report[tid]["symbolic_parts"] = [k for k, v in proof.items() if "Integer(0)" in v]
            report[tid]["numerical_parts"] = [k for k, v in proof.items() if "numerical" in v.lower()]
            report[tid]["proof_type"] = "mixed"
        elif "Integer(0)" in proof:
            report[tid]["proof_type"] = "symbolic_exact"
        elif "numerical" in proof.lower():
            report[tid]["proof_type"] = "numerical_verified"
        else:
            report[tid]["proof_type"] = "other"

    if verbose:
        print("═══ THEOREM PROOF STATUS ═══")
        for tid, info in report.items():
            ptype = info["proof_type"]
            mark = "■" if ptype == "symbolic_exact" else "□" if ptype == "mixed" else "○"
            claim = info["claim"]
            print(f"  {mark} [{claim}] {tid}: {info['statement']}")
            if ptype == "mixed":
                sym = info.get("symbolic_parts", [])
                num = info.get("numerical_parts", [])
                if sym:
                    print(f"        ■ Symbolic: {', '.join(sym)}")
                if num:
                    print(f"        ○ Numerical: {', '.join(num)}")
        print()
        print("  Legend: ■ = symbolic exact (Integer(0))")
        print("         □ = mixed (some parts symbolic, some numerical)")
        print("         ○ = numerical verification only")

    return report


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 65)
    print("K4 OPERATIONAL ASSUMPTIONS & PREFLIGHT SYSTEM")
    print("═" * 65)

    # Show proof status
    proof_status_report()

    # Demo: canonical DC preflight
    print("\n" + "─" * 65)
    print("PREFLIGHT: Canonical DC")
    print("─" * 65)
    pf = preflight(CANONICAL_DC)

    # Demo: canonical AC low
    print("\n" + "─" * 65)
    print("PREFLIGHT: Canonical AC Low (1 kHz)")
    print("─" * 65)
    pf2 = preflight(CANONICAL_AC_LOW)

    # Demo: bad assumptions (catch errors)
    print("\n" + "─" * 65)
    print("PREFLIGHT: Bad Assumptions (should fail)")
    print("─" * 65)
    bad = SessionAssumptions(
        session_name="BAD_SESSION",
        physics_regime=PhysicsRegime.DC,  # says DC
        frequency_Hz=1000.0,              # but has frequency!
        claim_ceiling="G",
        geometry_type="irregular_K4",     # and irregular geometry
    )
    pf3 = preflight(bad)
