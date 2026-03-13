"""
tests/test_artifacts.py — Artifact Layer Tests
================================================

Tests the write/read/inspect cycle for the artifact bundle.
Ensures manifest provenance, file layout, and round-trip integrity.
"""

import json
import math
import uuid
from datetime import datetime, timezone
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


def _make_artifact():
    """Build a full RunArtifact from BASIC-BZ for testing."""
    from k4_explorer.presets import BASIC_BZ
    from k4_explorer.context import build_context
    from k4_explorer.solver import solve_dc
    from k4_explorer.observables import evaluate_viewports
    from k4_explorer.contracts import RunArtifact, ClaimRecord, FrequencyRegime
    from k4_explorer.runtime import frozen_version
    from k4_artifacts.digest import solver_digest

    control_spec, geometry_spec = BASIC_BZ()
    ctx = build_context(geometry_spec)
    drive = solve_dc(control_spec, ctx)
    obs = evaluate_viewports(drive, ctx)

    claim = ClaimRecord(
        claim_class=ctx.claim_ceiling,
        assumptions=("regular_K4", "Biot-Savart", "quasi-static", "Config_D"),
        regime=FrequencyRegime.DC,
        frozen_version=frozen_version(),
        code_digest=solver_digest(),
        numerical_tolerances={"F0G_residual": ctx.F0G_residual},
        gate_status={"populated": True},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return RunArtifact(
        run_id=str(uuid.uuid4()),
        name="BASIC_BZ",
        description="Artifact layer test",
        control_spec=control_spec,
        geometry_spec=geometry_spec,
        drive=drive,
        observables=obs,
        claim_record=claim,
    )


class TestArtifactWrite:
    """Verify write_artifact creates the expected file layout."""

    def setup_method(self):
        self.artifact = _make_artifact()

    def test_write_creates_expected_files(self, tmp_path):
        from k4_artifacts.writer import write_artifact
        run_dir = write_artifact(self.artifact, str(tmp_path))

        expected = [
            "manifest.json", "spec.json", "drive.json",
            "observables.json", "claim.json", "environment.json", "notes.md",
        ]
        for fname in expected:
            assert (run_dir / fname).exists(), f"Missing: {fname}"
        assert (run_dir / "figures").is_dir(), "Missing figures/ directory"

    def test_manifest_contains_provenance(self, tmp_path):
        from k4_artifacts.writer import write_artifact, ARTIFACT_SCHEMA_VERSION
        run_dir = write_artifact(self.artifact, str(tmp_path))

        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8-sig"))

        # All provenance fields present
        assert "run_id" in manifest
        assert "name" in manifest
        assert "timestamp" in manifest
        assert "frozen_version" in manifest
        assert "code_digest" in manifest
        assert "frozen_digest" in manifest
        assert "claim_class" in manifest
        assert "regime" in manifest
        assert "artifact_schema_version" in manifest

        # Values are plausible
        assert manifest["name"] == "BASIC_BZ"
        assert manifest["claim_class"] == "G"
        assert manifest["regime"] == "DC"
        assert manifest["artifact_schema_version"] == ARTIFACT_SCHEMA_VERSION
        assert manifest["code_digest"].startswith("sha256:")
        assert manifest["frozen_digest"].startswith("sha256:")


class TestArtifactRead:
    """Verify reader validates and loads correctly."""

    def setup_method(self):
        self.artifact = _make_artifact()

    def test_load_manifest_validates(self, tmp_path):
        from k4_artifacts.reader import load_manifest

        # Missing manifest → FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_manifest(str(tmp_path / "nonexistent"))

        # Incomplete manifest → ValueError
        bad_dir = tmp_path / "bad_artifact"
        bad_dir.mkdir()
        (bad_dir / "manifest.json").write_text(
            json.dumps({"run_id": "x"}), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="missing required keys"):
            load_manifest(str(bad_dir))

    def test_load_manifest_roundtrip(self, tmp_path):
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.reader import load_manifest

        run_dir = write_artifact(self.artifact, str(tmp_path))
        manifest = load_manifest(str(run_dir))

        assert manifest["name"] == "BASIC_BZ"
        assert manifest["claim_class"] == "G"

    def test_load_json_roundtrip(self, tmp_path):
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.reader import load_json

        run_dir = write_artifact(self.artifact, str(tmp_path))

        drive = load_json(str(run_dir), "drive.json")
        assert "I_edge" in drive
        assert len(drive["I_edge"]) == 6

        obs = load_json(str(run_dir), "observables.json")
        assert isinstance(obs, list)
        assert len(obs) == 9  # 9 viewports

    def test_inspect_output(self, tmp_path):
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.reader import inspect_artifact

        run_dir = write_artifact(self.artifact, str(tmp_path))
        output = inspect_artifact(str(run_dir))

        # Administrative fields
        assert "BASIC_BZ" in output
        assert "[G]" in output

        # Provenance fields
        assert "Frozen digest:" in output
        assert "Schema:" in output

        # Headline viewport
        assert "VP-01" in output
        assert "|B|" in output
        assert "Selectivity" in output

    def test_inspect_graceful_without_vp01(self, tmp_path):
        """inspect_artifact shows first viewport if VP-01 is absent."""
        from k4_artifacts.writer import write_artifact
        from k4_artifacts.reader import inspect_artifact

        run_dir = write_artifact(self.artifact, str(tmp_path))

        # Rewrite observables without VP-01
        obs_path = run_dir / "observables.json"
        obs = json.loads(obs_path.read_text(encoding="utf-8-sig"))
        obs_no_vp01 = [o for o in obs if o.get("viewport_id") != "VP-01"]
        obs_path.write_text(json.dumps(obs_no_vp01, indent=2), encoding="utf-8")

        output = inspect_artifact(str(run_dir))
        # Should still show a headline viewport (first available)
        assert "|B|" in output
        assert "Viewports:" in output


class TestRuntimeFacade:
    """Verify the k4_explorer.runtime facade works."""

    def test_frozen_version_returns_string(self):
        from k4_explorer.runtime import frozen_version
        v = frozen_version()
        assert isinstance(v, str)
        assert len(v) > 0

    def test_check_frozen_succeeds(self):
        from k4_explorer.runtime import check_frozen
        # Should not raise in normal populated state
        check_frozen()
