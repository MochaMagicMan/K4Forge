"""
tests/test_figures.py — Figure Generation Tests
=================================================

Tests that the three standard figures are generated correctly
and integrated into the artifact pipeline.
"""

import json
from pathlib import Path

import numpy as np
import pytest

# Skip if frozen core is not populated
try:
    import k4_frozen
    k4_frozen.check_populated()
    FROZEN_AVAILABLE = True
except (ImportError, RuntimeError):
    FROZEN_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FROZEN_AVAILABLE, reason="k4_frozen not populated")


def _setup_run():
    """Run the BASIC-BZ pipeline, return (drive, obs, ctx)."""
    from k4_explorer.presets import BASIC_BZ
    from k4_explorer.context import build_context
    from k4_explorer.solver import solve_dc
    from k4_explorer.observables import evaluate_viewports

    control_spec, geometry_spec = BASIC_BZ()
    ctx = build_context(geometry_spec)
    drive = solve_dc(control_spec, ctx)
    obs = evaluate_viewports(drive, ctx)
    return drive, obs, ctx


class TestFigureGeneration:
    """Test individual figure functions."""

    def setup_method(self):
        self.drive, self.obs, self.ctx = _setup_run()

    def test_geometry_figure_created(self, tmp_path):
        from k4_viz.figures import plot_geometry
        path = plot_geometry(self.ctx.V, self.ctx.L, str(tmp_path))
        p = Path(path)
        assert p.exists(), "geometry.png not created"
        assert p.stat().st_size > 1024, "geometry.png too small (<1KB)"

    def test_field_slice_figure_created(self, tmp_path):
        from k4_viz.figures import plot_field_slice
        path = plot_field_slice(
            self.ctx.V, self.drive.I_edge, self.ctx.L,
            self.ctx.field_matrix_at, str(tmp_path),
        )
        p = Path(path)
        assert p.exists(), "field_slice.png not created"
        assert p.stat().st_size > 1024, "field_slice.png too small (<1KB)"

    def test_probe_summary_figure_created(self, tmp_path):
        from k4_viz.figures import plot_probe_summary
        path = plot_probe_summary(self.obs, str(tmp_path))
        p = Path(path)
        assert p.exists(), "probe_summary.png not created"
        assert p.stat().st_size > 1024, "probe_summary.png too small (<1KB)"

    def test_generate_run_figures_returns_paths(self, tmp_path):
        from k4_viz.figures import generate_run_figures
        fig_paths = generate_run_figures(
            V=self.ctx.V, L=self.ctx.L, I_edge=self.drive.I_edge,
            observables=self.obs, field_eval=self.ctx.field_matrix_at,
            output_dir=str(tmp_path),
        )
        assert isinstance(fig_paths, dict)
        assert len(fig_paths) == 3
        assert "geometry" in fig_paths
        assert "field_slice" in fig_paths
        assert "probe_summary" in fig_paths
        for name, path in fig_paths.items():
            assert Path(path).exists(), f"{name} figure not on disk"


class TestFiguresInArtifact:
    """Test figures integrated into the artifact pipeline."""

    def setup_method(self):
        self.drive, self.obs, self.ctx = _setup_run()

    def test_figures_in_artifact_dir(self, tmp_path):
        """Full pipeline: write artifact, generate figures, verify PNGs."""
        import uuid
        from datetime import datetime, timezone
        from k4_explorer.contracts import RunArtifact, ClaimRecord, FrequencyRegime
        from k4_explorer.runtime import frozen_version
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.digest import solver_digest
        from k4_viz.figures import generate_run_figures

        claim = ClaimRecord(
            claim_class=self.ctx.claim_ceiling,
            assumptions=("regular_K4", "Biot-Savart", "quasi-static", "Config_D"),
            regime=FrequencyRegime.DC,
            frozen_version=frozen_version(),
            code_digest=solver_digest(),
            numerical_tolerances={"F0G_residual": self.ctx.F0G_residual},
            gate_status={"populated": True},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        artifact = RunArtifact(
            run_id=str(uuid.uuid4()),
            name="BASIC_BZ",
            description="Figure integration test",
            control_spec=None,  # not needed for this test path
            geometry_spec=None,
            drive=self.drive,
            observables=self.obs,
            claim_record=claim,
        )

        # Write artifact (creates directory + figures/)
        run_dir = write_artifact(artifact, str(tmp_path))

        # Generate figures into figures/
        fig_dir = str(run_dir / "figures")
        fig_paths = generate_run_figures(
            V=self.ctx.V, L=self.ctx.L, I_edge=self.drive.I_edge,
            observables=self.obs, field_eval=self.ctx.field_matrix_at,
            output_dir=fig_dir,
        )

        # Assert all 3 PNGs exist in figures/
        for name in ["geometry", "field_slice", "probe_summary"]:
            png = run_dir / "figures" / f"{name}.png"
            assert png.exists(), f"Missing: {name}.png"
            assert png.stat().st_size > 1024, f"{name}.png too small"

    def test_manifest_records_figures(self, tmp_path):
        """Manifest includes figures key when figures are provided."""
        import uuid
        from datetime import datetime, timezone
        from k4_explorer.contracts import RunArtifact, ClaimRecord, FrequencyRegime
        from k4_explorer.runtime import frozen_version
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.digest import solver_digest

        claim = ClaimRecord(
            claim_class=self.ctx.claim_ceiling,
            assumptions=("regular_K4",),
            regime=FrequencyRegime.DC,
            frozen_version=frozen_version(),
            code_digest=solver_digest(),
            numerical_tolerances={},
            gate_status={"populated": True},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        artifact = RunArtifact(
            run_id=str(uuid.uuid4()),
            name="BASIC_BZ",
            description="Manifest figures test",
            control_spec=None,
            geometry_spec=None,
            drive=self.drive,
            observables=self.obs,
            claim_record=claim,
        )

        figures = {"geometry": "geometry.png", "field_slice": "field_slice.png",
                   "probe_summary": "probe_summary.png"}
        run_dir = write_artifact(artifact, str(tmp_path), figures=figures)

        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8-sig"))
        assert "figures" in manifest, "manifest missing 'figures' key"
        assert sorted(manifest["figures"]) == ["field_slice", "geometry", "probe_summary"]
