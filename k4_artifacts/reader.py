"""
k4_artifacts.reader — Artifact Loading & Validation
=====================================================

Loads a saved artifact bundle, validates structure, returns typed objects.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_manifest(artifact_dir: str) -> Dict[str, Any]:
    """Load and validate the manifest.json from an artifact directory."""
    d = Path(artifact_dir)
    manifest_path = d / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json in {artifact_dir}")

    manifest = json.loads(manifest_path.read_text())

    required_keys = {"run_id", "name", "timestamp", "frozen_version", "claim_class"}
    missing = required_keys - set(manifest.keys())
    if missing:
        raise ValueError(f"Manifest missing required keys: {missing}")

    return manifest


def load_json(artifact_dir: str, filename: str) -> Any:
    """Load a specific JSON file from the artifact directory."""
    path = Path(artifact_dir) / filename
    if not path.exists():
        raise FileNotFoundError(f"No {filename} in {artifact_dir}")
    return json.loads(path.read_text())


def inspect_artifact(artifact_dir: str) -> str:
    """Human-readable summary of an artifact."""
    manifest = load_manifest(artifact_dir)
    lines = [
        f"Run: {manifest['name']}",
        f"  ID:       {manifest['run_id'][:8]}...",
        f"  Time:     {manifest['timestamp']}",
        f"  Frozen:   {manifest['frozen_version']}",
        f"  Claim:    [{manifest['claim_class']}]",
    ]
    if "regime" in manifest:
        lines.append(f"  Regime:   {manifest['regime']}")
    if "code_digest" in manifest:
        lines.append(f"  Digest:   {manifest['code_digest']}")

    # Check for observables
    obs_path = Path(artifact_dir) / "observables.json"
    if obs_path.exists():
        obs = json.loads(obs_path.read_text())
        lines.append(f"  Viewports: {len(obs)} evaluated")

    return "\n".join(lines)
