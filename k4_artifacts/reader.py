"""
k4_artifacts.reader — Artifact Loading & Validation
=====================================================

Loads a saved artifact bundle, validates structure, returns typed objects.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict


def load_manifest(artifact_dir: str) -> Dict[str, Any]:
    """Load and validate the manifest.json from an artifact directory."""
    d = Path(artifact_dir)
    manifest_path = d / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json in {artifact_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

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
    return json.loads(path.read_text(encoding="utf-8-sig"))


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
    if "frozen_digest" in manifest:
        lines.append(f"  Frozen digest: {manifest['frozen_digest']}")
    if "artifact_schema_version" in manifest:
        lines.append(f"  Schema:   v{manifest['artifact_schema_version']}")

    # Check for observables and show headline viewport
    obs_path = Path(artifact_dir) / "observables.json"
    if obs_path.exists():
        obs = json.loads(obs_path.read_text(encoding="utf-8-sig"))
        lines.append(f"  Viewports: {len(obs)} evaluated")

        # Show headline viewport: VP-01 preferred, otherwise first available
        headline = next((o for o in obs if o.get("viewport_id") == "VP-01"), None)
        if headline is None and obs:
            headline = obs[0]
        if headline:
            vid = headline.get("viewport_id", "unknown")
            B = headline.get("B_total")
            B_mag = headline.get("B_magnitude")
            sel = headline.get("selectivity")
            claim = headline.get("claim_class")
            lines.append(f"  {vid}:")
            if B is not None:
                lines.append(f"    B = [{B[0]:.4e}, {B[1]:.4e}, {B[2]:.4e}] T")
            if B_mag is not None:
                lines.append(f"    |B| = {B_mag:.4e} T")
            if sel is not None:
                sel_str = "inf" if (sel is None or (isinstance(sel, float) and math.isinf(sel))) else f"{sel:.1f}"
                lines.append(f"    Selectivity = {sel_str}")
            if claim is not None:
                lines.append(f"    Claim: [{claim}]")

    return "\n".join(lines)
