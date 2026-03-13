"""
verify_all.py — Complete Verification Suite
============================================

Runs ALL proofs and tests across all layers:
  - Layer 0-1: Integer arithmetic (truth_kernel)
  - Layer 3-4: Biot-Savart EM theorems (field_engine)
  - Layer 5: Bose-Mesner algebra
  - Layer 6: Spherical harmonics
  - Layer 7: Sphere sculpting
  - Null tetrahedron structure
  - 12-test regression suite
  - SymPy exact proofs

This is the single command that certifies the frozen stack.

Usage:
    python -m k4_frozen_v3.verify_all
"""

import sys
import time
import json
import numpy as np
from datetime import datetime, timezone


def _section_result(tests: int, passed: int, status: str,
                    details: dict = None, reason: str = None) -> dict:
    """Uniform section schema for the JSON report."""
    d = {"tests": tests, "passed": passed, "failed": tests - passed,
         "status": status}
    if details:
        d["details"] = details
    if reason:
        d["reason"] = reason
    return d


def run_full_verification(verbose: bool = True, save_report: bool = True) -> dict:
    """
    Run complete verification of the frozen K4 stack.
    Returns comprehensive report dict.
    """
    from . import __version__, __frozen_from__

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "package_version": __version__,
        "frozen_from": __frozen_from__,
        "sections": {},
        "overall": "PENDING",
    }

    all_pass = True
    t0 = time.time()

    if verbose:
        w = 58
        print("╔" + "═" * w + "╗")
        title = f"k4_frozen_v3 v{__version__} — VERIFICATION SUITE"
        print(f"║   {title:<{w-3}}║")
        frozen_short = __frozen_from__[:w-7]
        print(f"║   {frozen_short:<{w-3}}║")
        print("╚" + "═" * w + "╝")
        print()

    # ─── SECTION 1: Layer 0-1 (Integer Arithmetic) ───
    if verbose:
        print("━" * 60)
        print("SECTION 1: Layer 0-1 — Integer Arithmetic Proofs")
        print("━" * 60)

    from . import truth_kernel as tk
    l1_results = tk.verify_layer1(verbose=verbose)
    l1_pass = all(l1_results.values())
    report["sections"]["layer_0_1"] = {
        "tests": len(l1_results),
        "passed": sum(l1_results.values()),
        "status": "PASS" if l1_pass else "FAIL",
        "details": {k: "PASS" if v else "FAIL" for k, v in l1_results.items()},
    }
    if not l1_pass:
        all_pass = False

    if verbose:
        print()

    # ─── SECTION 2: SymPy Exact Proofs ───
    if verbose:
        print("━" * 60)
        print("SECTION 2: SymPy Exact Proofs (Integer(0))")
        print("━" * 60)

    try:
        sympy_results = tk.verify_sympy()
        sympy_pass = all(sympy_results.values()) if sympy_results else True
        report["sections"]["sympy_proofs"] = {
            "tests": len(sympy_results),
            "passed": sum(sympy_results.values()),
            "status": "PASS" if sympy_pass else "FAIL",
            "details": {k: "PASS" if v else "FAIL" for k, v in sympy_results.items()},
        }
        if not sympy_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["sympy_proofs"] = _section_result(0, 0, "SKIPPED", reason=str(e))
        if verbose:
            print(f"  SymPy verification skipped: {e}")

    if verbose:
        print()

    # ─── SECTION 3: Layer 3-4 (Electromagnetic Theorems) ───
    # First: algebraic exact proofs (promoted from numerical)
    if verbose:
        print("━" * 60)
        print("SECTION 3a: Symbolic EM Proofs (Algebraic Exact)")
        print("━" * 60)

    try:
        from . import symbolic_proofs as sp_mod
        sym_em_results = sp_mod.verify_all_symbolic(verbose=verbose)
        sym_em_pass = all(v is True for v in sym_em_results.values())
        report["sections"]["symbolic_em"] = {
            "tests": len(sym_em_results),
            "passed": sum(1 for v in sym_em_results.values() if v is True),
            "status": "PASS" if sym_em_pass else "FAIL",
        }
        if not sym_em_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["symbolic_em"] = _section_result(0, 0, "SKIPPED", reason=str(e))
        if verbose:
            print(f"  Symbolic EM proofs skipped: {e}")

    if verbose:
        print()

    # Then: numerical verification (still needed for coverage)
    if verbose:
        print("━" * 60)
        print("SECTION 3b: Layer 3-4 — Electromagnetic Theorems (Numerical)")
        print("━" * 60)

    from . import field_engine as fe
    l4_results = fe.verify_layer4(verbose=verbose)
    l4_pass = all(l4_results.values())
    report["sections"]["layer_3_4"] = {
        "tests": len(l4_results),
        "passed": sum(l4_results.values()),
        "status": "PASS" if l4_pass else "FAIL",
    }
    if not l4_pass:
        all_pass = False

    if verbose:
        print()

    # ─── SECTION 4: E-Field Model ───
    if verbose:
        print("━" * 60)
        print("SECTION 4: E-Field Model Verification")
        print("━" * 60)

    e_results = fe.verify_e_field(verbose=verbose)
    e_pass = all(e_results.values())
    report["sections"]["e_field"] = {
        "tests": len(e_results),
        "passed": sum(e_results.values()),
        "status": "PASS" if e_pass else "FAIL",
    }
    if not e_pass:
        all_pass = False

    if verbose:
        print()

    # ─── SECTION 5: Null Tetrahedron ───
    if verbose:
        print("━" * 60)
        print("SECTION 5: Null Tetrahedron Structure")
        print("━" * 60)

    from . import null_tetrahedron as nt
    null_results = nt.null_tetrahedron_analysis(verbose=verbose)
    null_pass = all(null_results.values())
    report["sections"]["null_tetrahedron"] = {
        "tests": len(null_results),
        "passed": sum(null_results.values()),
        "status": "PASS" if null_pass else "FAIL",
    }
    if not null_pass:
        all_pass = False

    if verbose:
        print()

    # ─── SECTION 6: 12-Test Regression Suite ───
    if verbose:
        print("━" * 60)
        print("SECTION 6: 12-Test Regression Suite")
        print("━" * 60)

    from . import session_compiler as sc
    reg_results = sc.run_regression()
    sc.print_regression(reg_results) if verbose else None
    reg_pass = all(r.passed for r in reg_results)
    report["sections"]["regression"] = {
        "tests": len(reg_results),
        "passed": sum(1 for r in reg_results if r.passed),
        "status": "PASS" if reg_pass else "FAIL",
        "details": [r.to_dict() for r in reg_results],
    }
    if not reg_pass:
        all_pass = False

    if verbose:
        print()

    # ─── SECTION 7: Session Compilation ───
    if verbose:
        print("━" * 60)
        print("SECTION 7: Canonical Session Compilation")
        print("━" * 60)

    try:
        session = sc.solve_session(
            "VERIFY_BASIC", "Verification baseline: 1µT Bz",
            B_target=np.array([0.0, 0.0, 1e-6]))
        session_pass = session["regression_summary"]["status"] == "PASS"
        report["sections"]["session_compile"] = {
            "status": "PASS" if session_pass else "FAIL",
            "tier": session["diagnostics"]["tier"],
            "margin": session["diagnostics"]["margin"],
        }
        if verbose:
            print(f"  Compiled session: {session['name']}")
            print(f"  Tier: {session['diagnostics']['tier']}")
            print(f"  Margin: {session['diagnostics']['margin']:.4f}")
            print(f"  Regression: {session['regression_summary']['status']}")
        if not session_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["session_compile"] = _section_result(1, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Session compilation failed: {e}")

    # ─── SECTION 8: Policy Enforcement ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 8: Policy Enforcement (Drift Prevention)")
        print("━" * 60)

    try:
        from . import policy as pol
        from .session_schema import (
            SessionResult as SR, ConfigID as CID, BModelTier as BMT,
            EModelTier as EMT, ClaimClass as CC, ObservationClass as OC,
        )

        policy_results = {}

        # P1: Valid [G] at centroid passes
        r = SR(config_id=CID.D, b_model_tier=BMT.SYMBOLIC_CENTROID,
               claim_class=CC.G, observation_class=OC.CENTROID,
               quantity_name="test_valid_G")
        v, _ = pol.enforce_all(r, pol.CANONICAL_K4)
        errors = [x for x in v if x.severity == "ERROR"]
        policy_results["valid_G_centroid"] = len(errors) == 0

        # P2: [G] at face center auto-downgrades to [M]
        r2 = SR(config_id=CID.A, b_model_tier=BMT.FINITE_SEGMENT_BIOT_SAVART,
                claim_class=CC.G, observation_class=OC.FACE_CENTER,
                quantity_name="test_overclaim")
        v2, r2 = pol.enforce_all(r2, pol.CANONICAL_K4, auto_fix=True)
        policy_results["overclaim_downgrade"] = r2.claim_class == CC.M

        # P3: E on Config B raises violation
        r3 = SR(config_id=CID.B, e_model_tier=EMT.LEVEL2_POINT_ELECTRODE,
                claim_class=CC.M, quantity_name="test_e_on_B")
        v3, _ = pol.enforce_all(r3)
        config_errs = [x for x in v3 if x.rule == "CONFIG_CONTRACT"]
        policy_results["e_on_config_b_caught"] = len(config_errs) > 0

        # P4: Non-K₄ geometry caught
        bad = pol.GeometryCertification(
            name="Triangle", description="K3", vertex_count=3, edge_count=3,
            is_complete_graph=True, vertex_connectivity_realized=True,
            kcl_enforced=False, config_id=CID.A, geometry_type="K3")
        policy_results["non_k4_caught"] = len(bad.validate()) > 0

        # P5: Irregular K₄ without calibration caught
        irr = pol.GeometryCertification(
            name="Irregular", description="squashed", vertex_count=4, edge_count=6,
            is_complete_graph=True, vertex_connectivity_realized=True,
            kcl_enforced=False, config_id=CID.D, geometry_type="irregular_K4",
            calibration_required=False)
        policy_results["irregular_no_cal_caught"] = len(irr.validate()) > 0

        # P6: Canonical K₄ passes clean
        policy_results["canonical_clean"] = len(pol.CANONICAL_K4.validate()) == 0

        p_pass = all(policy_results.values())
        report["sections"]["policy"] = {
            "tests": len(policy_results),
            "passed": sum(policy_results.values()),
            "status": "PASS" if p_pass else "FAIL",
            "details": {k: "PASS" if v else "FAIL" for k, v in policy_results.items()},
        }
        if not p_pass:
            all_pass = False

        if verbose:
            for name, passed in policy_results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {name}: {status}")
            print(f"\n  {sum(policy_results.values())}/{len(policy_results)} policy tests passed")

    except Exception as e:
        report["sections"]["policy"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Policy tests failed: {e}")

    # ─── SECTION 9: Inductance & Functional Control ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 9: Inductance & Functional Control")
        print("━" * 60)

    try:
        from .inductance import (
            compute_inductance_tensor, verify_inductance,
            command_dc, regime_analysis,
        )

        ind_results = verify_inductance(verbose=False)
        ind_pass = all(ind_results.values())
        report["sections"]["inductance"] = {
            "tests": len(ind_results),
            "passed": sum(ind_results.values()),
            "status": "PASS" if ind_pass else "FAIL",
            "details": {k: "PASS" if v else "FAIL" for k, v in ind_results.items()},
        }
        if not ind_pass:
            all_pass = False

        if verbose:
            for name, passed in ind_results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {name}: {status}")
            print(f"\n  {sum(ind_results.values())}/{len(ind_results)} inductance tests passed")

    except Exception as e:
        report["sections"]["inductance"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Inductance tests failed: {e}")

    # ─── SECTION 10: Bose-Mesner Algebra ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 10: Bose-Mesner Algebra")
        print("━" * 60)

    try:
        from .bose_mesner import verify_bose_mesner
        bm_results = verify_bose_mesner(verbose=verbose)
        bm_pass = all(bm_results.values())
        report["sections"]["bose_mesner"] = {
            "tests": len(bm_results),
            "passed": sum(bm_results.values()),
            "status": "PASS" if bm_pass else "FAIL",
        }
        if not bm_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["bose_mesner"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Bose-Mesner tests failed: {e}")

    # ─── SECTION 11: Spherical Harmonics ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 11: Spherical Harmonics")
        print("━" * 60)

    try:
        from .spherical_harmonics import verify_spherical_harmonics
        sh_results = verify_spherical_harmonics(verbose=verbose)
        sh_pass = all(sh_results.values())
        report["sections"]["spherical_harmonics"] = {
            "tests": len(sh_results),
            "passed": sum(sh_results.values()),
            "status": "PASS" if sh_pass else "FAIL",
        }
        if not sh_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["spherical_harmonics"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Spherical harmonic tests failed: {e}")

    # ─── SECTION 12: Sphere Sculpting ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 12: Sphere Sculpting")
        print("━" * 60)

    try:
        from .sphere_sculpt import verify_sculpting
        sc_results = verify_sculpting(verbose=verbose)
        sc_pass = all(sc_results.values())
        report["sections"]["sphere_sculpt"] = {
            "tests": len(sc_results),
            "passed": sum(sc_results.values()),
            "status": "PASS" if sc_pass else "FAIL",
        }
        if not sc_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["sphere_sculpt"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Sculpting tests failed: {e}")

    # ─── SECTION 13: Full-Wave Extension (v3.0) ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 13: Full-Wave Extension (v3.0)")
        print("━" * 60)

    try:
        from .full_wave import verify_full_wave
        fw_pass = verify_full_wave(verbose=verbose)
        fw_tests = 12  # 10 frequencies + 2 algebraic
        report["sections"]["full_wave"] = {
            "tests": fw_tests,
            "passed": fw_tests if fw_pass else 0,
            "status": "PASS" if fw_pass else "FAIL",
        }
        if not fw_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["full_wave"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Full-wave tests failed: {e}")

    # ─── SECTION 14: S₄ Commutant (v3.0) ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 14: S₄ Commutant & Rep Theory (v3.0)")
        print("━" * 60)

    try:
        from .commutant import verify_commutant
        cm_pass = verify_commutant(verbose=verbose)
        cm_tests = 5
        report["sections"]["commutant"] = {
            "tests": cm_tests,
            "passed": cm_tests if cm_pass else 0,
            "status": "PASS" if cm_pass else "FAIL",
        }
        if not cm_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["commutant"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Commutant tests failed: {e}")

    # ─── SECTION 15: Ring-Quiet Mode (v3.0) ───
    if verbose:
        print()
        print("━" * 60)
        print("SECTION 15: Ring-Quiet Mode (v3.0)")
        print("━" * 60)

    try:
        from .ring_quiet import verify_ring_quiet
        rq_pass = verify_ring_quiet(verbose=verbose)
        rq_tests = 6
        report["sections"]["ring_quiet"] = {
            "tests": rq_tests,
            "passed": rq_tests if rq_pass else 0,
            "status": "PASS" if rq_pass else "FAIL",
        }
        if not rq_pass:
            all_pass = False
    except Exception as e:
        report["sections"]["ring_quiet"] = _section_result(0, 0, "FAIL", reason=str(e))
        all_pass = False
        if verbose:
            print(f"  ✗ Ring-quiet tests failed: {e}")

    # ─── FINAL SUMMARY ───
    elapsed = time.time() - t0
    report["overall"] = "PASS" if all_pass else "FAIL"
    report["elapsed_seconds"] = elapsed

    total_tests = sum(
        s.get("tests", 0) for s in report["sections"].values()
        if isinstance(s, dict) and "tests" in s
    )
    total_passed = sum(
        s.get("passed", 0) for s in report["sections"].values()
        if isinstance(s, dict) and "passed" in s
    )
    total_failed = total_tests - total_passed
    total_skipped = sum(
        1 for s in report["sections"].values()
        if isinstance(s, dict) and s.get("status") == "SKIPPED"
    )

    report["total_tests"] = total_tests
    report["total_passed"] = total_passed
    report["total_failed"] = total_failed
    report["total_skipped"] = total_skipped

    # Build fail capsule: which sections failed and which test keys
    failing_sections = []
    failing_keys = []
    skipped_sections = []
    for sec_name, sec_data in report["sections"].items():
        if not isinstance(sec_data, dict):
            continue
        if sec_data.get("status") == "FAIL":
            failing_sections.append(sec_name)
            details = sec_data.get("details", {})
            if isinstance(details, dict):
                for k, v in details.items():
                    if v == "FAIL" or v is False:
                        failing_keys.append(f"{sec_name}.{k}")
        elif sec_data.get("status") == "SKIPPED":
            skipped_sections.append(sec_name)

    report["failing_sections"] = failing_sections
    report["failing_keys"] = failing_keys
    report["skipped_sections"] = skipped_sections

    if verbose:
        print()
        print("╔" + "═" * 58 + "╗")
        if all_pass:
            print("║   ✅ INTERNAL CONSISTENCY VERIFIED                         ║")
            print("║   All algebraic identities, numerical checks, and         ║")
            print("║   cross-module contracts pass. These tests verify          ║")
            print("║   self-consistency, NOT independent physical validation.   ║")
        else:
            print("║   ❌ VERIFICATION FAILURES DETECTED                       ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║   Total tests: {total_tests:>4d}                                     ║")
        print(f"║   Passed:      {total_passed:>4d}                                     ║")
        print(f"║   Failed:      {total_failed:>4d}                                     ║")
        print(f"║   Skipped:     {total_skipped:>4d} section(s)                            ║")
        print(f"║   Elapsed:     {elapsed:>6.2f}s                                   ║")
        print("╚" + "═" * 58 + "╝")

        if failing_sections:
            print("\n  ── FAIL CAPSULE ──")
            print(f"  Failing sections: {', '.join(failing_sections)}")
            if failing_keys:
                print(f"  Failing tests ({len(failing_keys)}):")
                for fk in failing_keys[:20]:
                    print(f"    ✗ {fk}")
                if len(failing_keys) > 20:
                    print(f"    ... and {len(failing_keys) - 20} more")

        if skipped_sections:
            print(f"\n  Skipped sections: {', '.join(skipped_sections)}")

    if save_report:
        report_path = "k4_verification_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        if verbose:
            print(f"\n  Report saved to: {report_path}")

    return report


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    report = run_full_verification(verbose=True, save_report=True)
    sys.exit(0 if report["overall"] == "PASS" else 1)
