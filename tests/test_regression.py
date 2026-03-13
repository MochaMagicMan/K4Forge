"""
tests/test_regression.py — I_edge Regression & Reproducibility
==============================================================

Captures the exact I_edge values from BASIC-BZ and asserts they
match within 1e-12 on rerun.  Also verifies that two independent
runs of the full pipeline produce bitwise-identical observables.

Marks: @pytest.mark.regression
"""

import numpy as np
import pytest

# Skip all tests if frozen core is not populated
try:
    import k4_frozen
    k4_frozen.check_populated()
    FROZEN_AVAILABLE = True
except (ImportError, RuntimeError):
    FROZEN_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FROZEN_AVAILABLE, reason="k4_frozen not populated")


def _run_basic_bz():
    """Run the BASIC-BZ pipeline end-to-end, return (drive, observables)."""
    from k4_explorer.presets import BASIC_BZ
    from k4_explorer.context import build_context
    from k4_explorer.solver import solve_dc
    from k4_explorer.observables import evaluate_viewports

    control_spec, geometry_spec = BASIC_BZ()
    ctx = build_context(geometry_spec)
    drive = solve_dc(control_spec, ctx)
    obs = evaluate_viewports(drive, ctx)
    return drive, obs


# ═══════════════════════════════════════════════════════════════════
# Regression: pinned I_edge values from BASIC-BZ
# ═══════════════════════════════════════════════════════════════════

# These are the exact I_edge values produced by the BASIC-BZ preset
# on the regular K4 geometry (L=0.1m, B_target=(0,0,10µT), DC).
# If these drift, the engine has changed.
EXPECTED_I_EDGE = np.array([
    -0.76546554,
     0.76546554,
     0.0,
     0.0,
    -0.76546554,
     0.76546554,
])

EXPECTED_W = np.array([0.0, -0.76546554, -0.76546554])
EXPECTED_U_COIL = np.array([0.0, 0.0, 0.0])


@pytest.mark.regression
class TestIEdgeRegression:
    """Pin the exact I_edge values from BASIC-BZ."""

    def setup_method(self):
        self.drive, self.obs = _run_basic_bz()

    def test_I_edge_values(self):
        """I_edge must match pinned values within 1e-12."""
        np.testing.assert_allclose(
            self.drive.I_edge, EXPECTED_I_EDGE, atol=1e-12,
            err_msg="I_edge regression: values have drifted from baseline",
        )

    def test_w_values(self):
        """Cycle weights must match pinned values within 1e-12."""
        np.testing.assert_allclose(
            self.drive.w, EXPECTED_W, atol=1e-12,
            err_msg="w regression: cycle weights have drifted from baseline",
        )

    def test_u_coil_values(self):
        """Cut weights must be exactly zero for BASIC-BZ."""
        np.testing.assert_allclose(
            self.drive.u_coil, EXPECTED_U_COIL, atol=1e-12,
            err_msg="u_coil regression: cut weights have drifted from baseline",
        )

    def test_B_centroid_exact(self):
        """B at centroid must be exactly (0, 0, 10µT)."""
        vp01 = next(o for o in self.obs if o.viewport_id == "VP-01")
        np.testing.assert_allclose(
            vp01.B_total, [0.0, 0.0, 1e-05], atol=1e-12,
            err_msg="B at centroid has drifted from (0, 0, 10µT)",
        )


# ═══════════════════════════════════════════════════════════════════
# Reproducibility: two runs must produce identical results
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.regression
class TestReproducibility:
    """Two independent runs of BASIC-BZ must produce identical results."""

    def setup_method(self):
        self.drive_a, self.obs_a = _run_basic_bz()
        self.drive_b, self.obs_b = _run_basic_bz()

    def test_I_edge_reproducible(self):
        """I_edge must be bitwise identical across runs."""
        assert np.array_equal(self.drive_a.I_edge, self.drive_b.I_edge), \
            "I_edge differs between two runs of the same preset"

    def test_w_reproducible(self):
        """Cycle weights must be bitwise identical across runs."""
        assert np.array_equal(self.drive_a.w, self.drive_b.w), \
            "w differs between two runs of the same preset"

    def test_u_coil_reproducible(self):
        """Cut weights must be bitwise identical across runs."""
        assert np.array_equal(self.drive_a.u_coil, self.drive_b.u_coil), \
            "u_coil differs between two runs of the same preset"

    def test_observables_reproducible(self):
        """All observable B_total and B_magnitude must match across runs."""
        for oa, ob in zip(self.obs_a, self.obs_b):
            assert oa.viewport_id == ob.viewport_id, \
                f"Viewport ordering mismatch: {oa.viewport_id} vs {ob.viewport_id}"
            assert np.array_equal(oa.B_total, ob.B_total), \
                f"{oa.viewport_id}: B_total differs between runs"
            assert oa.B_magnitude == ob.B_magnitude, \
                f"{oa.viewport_id}: B_magnitude differs between runs"
            assert oa.selectivity == ob.selectivity, \
                f"{oa.viewport_id}: selectivity differs between runs"
