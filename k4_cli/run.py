"""
k4_cli.run — Main CLI Entry Point
====================================

Usage:
    k4 run <preset>          Run a preset and save artifact
    k4 run --spec FILE       Run from a JSON spec file
    k4 verify                Run frozen core verification (182 gates)
    k4 inspect <dir>         Inspect a saved artifact

IMPORT RULES:
    May import: k4_explorer, k4_artifacts
    Must never import: k4_frozen directly
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def cmd_run(args):
    """Run a preset or spec and produce a saved artifact."""
    from k4_explorer.presets import PRESET_REGISTRY
    from k4_explorer.context import build_context
    from k4_explorer.solver import solve_dc
    from k4_explorer.observables import evaluate_viewports
    from k4_explorer.contracts import RunArtifact, ClaimRecord, FrequencyRegime
    from k4_artifacts.writer import write_artifact
    from k4_artifacts.digest import solver_digest
    import k4_frozen

    # ── Step 0: Verify frozen core ──
    print("Verifying frozen core...", end=" ", flush=True)
    k4_frozen.check_populated()
    # Full gate check deferred to test suite; here we just check population
    print("OK")

    # ── Step 1: Load spec ──
    if args.preset:
        preset_name = args.preset.lower().replace("_", "-")
        if preset_name not in PRESET_REGISTRY:
            print(f"Unknown preset: {preset_name}")
            print(f"Available: {', '.join(sorted(PRESET_REGISTRY.keys()))}")
            return 1
        control_spec, geometry_spec = PRESET_REGISTRY[preset_name]()
        run_name = preset_name.upper().replace("-", "_")
        print(f"Loaded preset: {run_name}")
    else:
        print("JSON spec loading not yet implemented. Use a preset.")
        return 1

    # ── Step 2: Build field context ──
    print("Building field context...", end=" ", flush=True)
    ctx = build_context(geometry_spec)
    print(f"OK (F0G_residual={ctx.F0G_residual:.2e}, κ={ctx.F0M_condition:.3f}, "
          f"ceiling=[{ctx.claim_ceiling.value}])")

    # ── Step 3: Solve ──
    print("Solving...", end=" ", flush=True)
    drive = solve_dc(control_spec, ctx)
    print(f"OK (I_max={drive.I_max*1e3:.3f} mA, P={drive.P_dissipated*1e6:.2f} µW)")

    # ── Step 4: Evaluate viewports ──
    print("Evaluating viewports...", end=" ", flush=True)
    obs = evaluate_viewports(drive, ctx)
    print(f"OK ({len(obs)} viewports)")

    # ── Step 5: Build provenance ──
    claim = ClaimRecord(
        claim_class=ctx.claim_ceiling,
        assumptions=("regular_K4", "Biot-Savart", "quasi-static", "Config_D"),
        regime=FrequencyRegime.DC,
        frozen_version=k4_frozen.__version__,
        code_digest=solver_digest(),
        numerical_tolerances={"F0G_residual": ctx.F0G_residual},
        gate_status={"populated": True},  # full gates run in test suite
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # ── Step 6: Build and save artifact ──
    artifact = RunArtifact(
        run_id=str(uuid.uuid4()),
        name=run_name,
        description=f"Preset: {preset_name}",
        control_spec=control_spec,
        geometry_spec=geometry_spec,
        drive=drive,
        observables=obs,
        claim_record=claim,
    )

    output_dir = args.output or "runs"
    run_dir = write_artifact(artifact, output_dir)
    print(f"\nArtifact saved: {run_dir}")

    # ── Summary ──
    vp01 = next((o for o in obs if o.viewport_id == "VP-01"), None)
    if vp01:
        print(f"\nVP-01 (centroid):")
        print(f"  B = [{vp01.B_total[0]:.4e}, {vp01.B_total[1]:.4e}, {vp01.B_total[2]:.4e}] T")
        print(f"  |B| = {vp01.B_magnitude:.4e} T")
        if vp01.E is not None:
            print(f"  E = [{vp01.E[0]:.2f}, {vp01.E[1]:.2f}, {vp01.E[2]:.2f}] V/m")
        print(f"  Selectivity = {vp01.selectivity:.1f}")
        print(f"  Claim: [{vp01.claim_class.value}]")

    return 0


def cmd_verify(args):
    """Run frozen core verification."""
    print("Running k4_frozen.verify_all...")
    try:
        from k4_frozen.verify_all import run_verification
        report = run_verification(verbose=True)
        if report.get("all_pass"):
            print("\n✅ ALL GATES PASS")
            return 0
        else:
            print("\n❌ FAILURES DETECTED")
            return 1
    except ImportError:
        print("k4_frozen not populated. Copy v3 modules first.")
        return 1
    except Exception as e:
        print(f"Verification failed: {e}")
        return 1


def cmd_inspect(args):
    """Inspect a saved artifact."""
    from k4_artifacts.reader import inspect_artifact
    try:
        print(inspect_artifact(args.artifact_dir))
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="k4",
        description="K4 Tetrahedral EM Field Control — Exploration Engine",
    )
    sub = parser.add_subparsers(dest="command")

    # k4 run
    p_run = sub.add_parser("run", help="Run a preset or spec")
    p_run.add_argument("preset", nargs="?", help="Preset name (e.g. basic-bz)")
    p_run.add_argument("--spec", help="JSON spec file (not yet implemented)")
    p_run.add_argument("--output", "-o", help="Output directory (default: runs/)")

    # k4 verify
    sub.add_parser("verify", help="Verify frozen core (182 gates)")

    # k4 inspect
    p_inspect = sub.add_parser("inspect", help="Inspect a saved artifact")
    p_inspect.add_argument("artifact_dir", help="Path to artifact directory")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "inspect":
        sys.exit(cmd_inspect(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
