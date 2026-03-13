"""
k4_artifacts.writer — Artifact Serialization
==============================================

Writes a RunArtifact to a directory of JSON files.

Directory layout:
    {run_dir}/
        manifest.json       — top-level identity and summary
        spec.json            — ControlSpec + GeometrySpec
        drive.json           — DriveSpec (the solution)
        observables.json     — List[ObservableBundle]
        claim.json           — ClaimRecord (provenance)
        environment.json     — Python version, platform, dependency versions
        notes.md             — free-form notes
        figures/             — generated figures (if any)
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np

from k4_explorer.contracts import (
    ControlSpec, GeometrySpec, DriveSpec, ObservableBundle,
    ClaimRecord, RunArtifact, ClaimClass, SymmetryClass,
    FrequencyRegime, RegressionStatus, ConfigID,
)
from . import digest as dg


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays and enums."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, (ClaimClass, SymmetryClass, FrequencyRegime,
                            RegressionStatus, ConfigID)):
            return obj.value
        return super().default(obj)


def _serialize(obj) -> dict:
    """Convert a dataclass to a JSON-safe dict."""
    if hasattr(obj, '__dataclass_fields__'):
        d = {}
        for k in obj.__dataclass_fields__:
            v = getattr(obj, k)
            if isinstance(v, np.ndarray):
                d[k] = v.tolist()
            elif hasattr(v, '__dataclass_fields__'):
                d[k] = _serialize(v)
            elif isinstance(v, (list, tuple)):
                d[k] = [_serialize(x) if hasattr(x, '__dataclass_fields__') else x for x in v]
            elif isinstance(v, dict):
                d[k] = {kk: (_serialize(vv) if hasattr(vv, '__dataclass_fields__') else vv)
                         for kk, vv in v.items()}
            elif isinstance(v, (ClaimClass, SymmetryClass, FrequencyRegime,
                                RegressionStatus, ConfigID)):
                d[k] = v.value
            elif callable(v):
                d[k] = "<callable>"  # can't serialize functions
            else:
                d[k] = v
        return d
    return obj


def write_artifact(artifact: RunArtifact,
                   output_dir: str,
                   notes: str = "") -> Path:
    """
    Write a RunArtifact to a directory.

    Returns the path to the artifact directory.
    """
    # Generate run ID if not set
    if not artifact.run_id:
        artifact.run_id = str(uuid.uuid4())

    run_id_short = artifact.run_id[:8]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_name = artifact.name.lower().replace(" ", "_").replace("-", "_")[:30]
    dir_name = f"{date_str}_{safe_name}_{run_id_short}"

    run_dir = Path(output_dir) / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "figures").mkdir(exist_ok=True)

    # Manifest
    manifest = {
        "run_id": artifact.run_id,
        "name": artifact.name,
        "description": artifact.description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frozen_version": artifact.claim_record.frozen_version if artifact.claim_record else "unknown",
        "code_digest": dg.solver_digest(),
        "claim_class": artifact.claim_record.claim_class.value if artifact.claim_record else "M",
        "regime": artifact.claim_record.regime.value if artifact.claim_record else "DC",
        "files": ["spec.json", "drive.json", "observables.json", "claim.json", "environment.json"],
    }
    _write_json(run_dir / "manifest.json", manifest)

    # Spec (inputs)
    spec_data = {
        "control_spec": _serialize(artifact.control_spec),
        "geometry_spec": _serialize(artifact.geometry_spec),
    }
    _write_json(run_dir / "spec.json", spec_data)

    # Drive (solution)
    _write_json(run_dir / "drive.json", _serialize(artifact.drive))

    # Observables
    obs_list = [_serialize(o) for o in artifact.observables]
    _write_json(run_dir / "observables.json", obs_list)

    # Claim record
    if artifact.claim_record:
        _write_json(run_dir / "claim.json", _serialize(artifact.claim_record))

    # Environment
    _write_json(run_dir / "environment.json", dg.environment_info())

    # Notes
    all_notes = notes or artifact.notes or ""
    if artifact.ledger_entries:
        all_notes += "\n\n## Ledger\n" + "\n".join(f"- {e}" for e in artifact.ledger_entries)
    (run_dir / "notes.md").write_text(all_notes)

    return run_dir


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, cls=_NumpyEncoder))
