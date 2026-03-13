"""
tests/test_vertical_slice.py — End-to-End Vertical Slice
==========================================================

Runs the BASIC-BZ preset through the full pipeline:
    preset → geometry → context → solver → observables → artifact

This is THE regression anchor. If this test fails, the engine has drifted.

Marks: @pytest.mark.vertical
"""

import json
import numpy as np
from pathlib import Path
import pytest
import tempfile

# Skip all tests if frozen core is not populated
try:
    import k4_frozen
    k4_frozen.check_populated()
    FROZEN_AVAILABLE = True
except (ImportError, RuntimeError):
    FROZEN_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FROZEN_AVAILABLE, reason="k4_frozen not populated")


@pytest.mark.vertical
class TestVerticalSlice:
    """End-to-end pipeline test using BASIC-BZ preset."""

    def setup_method(self):
        """Build context and solve once for all tests in this class."""
        from k4_explorer.presets import BASIC_BZ
        from k4_explorer.context import build_context
        from k4_explorer.solver import solve_dc
        from k4_explorer.observables import evaluate_viewports

        self.control_spec, self.geometry_spec = BASIC_BZ()
        self.ctx = build_context(self.geometry_spec)
        self.drive = solve_dc(self.control_spec, self.ctx)
        self.obs = evaluate_viewports(self.drive, self.ctx)

    # ── Geometry checks ──

    def test_geometry_is_regular(self):
        assert self.geometry_spec.symmetry_class.value == "Td_regular"

    def test_context_claim_ceiling(self):
        from k4_explorer.contracts import ClaimClass
        assert self.ctx.claim_ceiling == ClaimClass.G

    def test_F0G_residual(self):
        """F₀·G must be < 10⁻¹² for regular K4."""
        assert self.ctx.F0G_residual < 1e-12, \
            f"F0G_residual = {self.ctx.F0G_residual} — cut annihilation violated"

    def test_F0M_condition(self):
        """κ(F₀·M) must be ≈ 2.0 for regular K4."""
        assert abs(self.ctx.F0M_condition - 2.0) < 0.01, \
            f"F0M_condition = {self.ctx.F0M_condition} — expected ≈ 2.0"

    # ── Solver checks ──

    def test_decomposition_invariant(self):
        """I_edge == M @ w + G @ u_coil."""
        assert self.drive.verify_decomposition(self.ctx.M, self.ctx.G, tol=1e-12)

    def test_B_at_centroid_accuracy(self):
        """B achieved at centroid must match target to < 10⁻¹²."""
        vp01 = next(o for o in self.obs if o.viewport_id == "VP-01")
        B_target = np.array(self.control_spec.B_target)
        B_achieved = vp01.B_total
        error = np.linalg.norm(B_achieved - B_target)
        B_mag = np.linalg.norm(B_target)
        rel_error = error / B_mag if B_mag > 0 else 0
        assert rel_error < 1e-12, \
            f"B error at centroid: {rel_error:.2e} (target {B_target}, got {B_achieved})"

    def test_cut_annihilation_at_centroid(self):
        """B_cut at centroid must be negligible (F₀·G = 0)."""
        vp01 = next(o for o in self.obs if o.viewport_id == "VP-01")
        B_cut_mag = np.linalg.norm(vp01.B_cut)
        B_total_mag = vp01.B_magnitude
        ratio = B_cut_mag / B_total_mag if B_total_mag > 0 else 0
        assert ratio < 1e-12, \
            f"Cut contribution at centroid: {ratio:.2e} of total (should be ~0)"

    def test_selectivity_at_centroid(self):
        """Selectivity at centroid must be very large (cycle >> cut)."""
        vp01 = next(o for o in self.obs if o.viewport_id == "VP-01")
        assert vp01.selectivity > 1e10, \
            f"Selectivity at centroid: {vp01.selectivity} (expected >> 1)"

    def test_nine_viewports_evaluated(self):
        """All 9 canonical viewports must be present."""
        vp_ids = {o.viewport_id for o in self.obs}
        expected = {f"VP-{i:02d}" for i in range(1, 10)}
        assert vp_ids == expected, f"Missing viewports: {expected - vp_ids}"

    # ── Observable physics ──

    def test_selectivity_at_viewports(self):
        """Selectivity behavior across viewports.
        
        BASIC-BZ has u_coil = 0, so B_cut = 0 everywhere and selectivity = inf.
        That is correct — with no cut drive, cycle dominates trivially.
        The meaningful test is: selectivity at centroid ≥ selectivity off-centroid.
        When both channels are active (e.g. NULL-ORBIT preset), selectivity
        should strictly decrease from centroid outward.
        """
        sel_01 = next(o for o in self.obs if o.viewport_id == "VP-01").selectivity
        
        if np.isinf(sel_01):
            # No cut drive active — all selectivities should be inf
            for o in self.obs:
                assert np.isinf(o.selectivity) or o.selectivity > 1e10, \
                    f"{o.viewport_id}: selectivity = {o.selectivity} (expected inf with zero cut)"
        else:
            # Cut drive active — selectivity should decrease outward
            sel_04 = next(o for o in self.obs if o.viewport_id == "VP-04").selectivity
            sel_07 = next(o for o in self.obs if o.viewport_id == "VP-07").selectivity
            assert sel_01 > sel_04 > sel_07, \
                f"Selectivity not decreasing: {sel_01:.1f} > {sel_04:.1f} > {sel_07:.1f}"

    # ── Artifact serialization ──

    def test_artifact_roundtrip(self):
        """Artifact writes to disk and loads cleanly."""
        from k4_explorer.contracts import RunArtifact, ClaimRecord, FrequencyRegime, ClaimClass
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.reader import load_manifest

        claim = ClaimRecord(
            claim_class=ClaimClass.G,
            assumptions=("regular_K4", "Biot-Savart", "DC"),
            regime=FrequencyRegime.DC,
            frozen_version=k4_frozen.__version__,
            code_digest="sha256:test",
            numerical_tolerances={"F0G_residual": self.ctx.F0G_residual},
            gate_status={"test": True},
            timestamp="2026-03-12T00:00:00Z",
        )

        artifact = RunArtifact(
            run_id="test-000",
            name="BASIC_BZ_TEST",
            description="Vertical slice test",
            control_spec=self.control_spec,
            geometry_spec=self.geometry_spec,
            drive=self.drive,
            observables=self.obs,
            claim_record=claim,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = write_artifact(artifact, tmpdir)
            assert run_dir.exists()
            assert (run_dir / "manifest.json").exists()
            assert (run_dir / "drive.json").exists()
            assert (run_dir / "observables.json").exists()

            manifest = load_manifest(str(run_dir))
            assert manifest["name"] == "BASIC_BZ_TEST"
            assert manifest["claim_class"] == "G"
            assert manifest["frozen_version"] == k4_frozen.__version__


@pytest.mark.vertical
def test_decomposition_roundtrip():
    """w → I_edge → decompose → w must be exact."""
    if not FROZEN_AVAILABLE:
        pytest.skip("k4_frozen not populated")

    from k4_frozen import truth_kernel as tk
    M = tk.M.astype(float)
    G = tk.G.astype(float)

    # Arbitrary test vector
    w_orig = np.array([1.0, -0.5, 0.3])
    u_orig = np.array([0.2, -0.1, 0.4])
    I_edge = M @ w_orig + G @ u_orig

    # Recover via pseudoinverse
    MtM_inv = np.linalg.inv(M.T @ M)
    GtG_inv = np.linalg.inv(G.T @ G)
    w_rec = MtM_inv @ M.T @ I_edge
    u_rec = GtG_inv @ G.T @ I_edge

    assert np.allclose(w_rec, w_orig, atol=1e-14), \
        f"Cycle recovery failed: {w_rec} vs {w_orig}"
    assert np.allclose(u_rec, u_orig, atol=1e-14), \
        f"Cut recovery failed: {u_rec} vs {u_orig}"
