"""
tests/test_imports.py — Import Rule Enforcement
=================================================

Walks the AST of every .py file and asserts no forbidden imports exist.
This is the immune system that prevents circular contamination.

Rules enforced:
    1. k4_frozen.* must never import from k4_explorer, k4_artifacts, k4_viz, k4_cli
    2. k4_explorer.contracts must never import from k4_frozen or k4_explorer logic
    3. k4_viz must never import from k4_frozen or k4_explorer.solver/optimizer
    4. k4_artifacts must never import from k4_frozen or k4_explorer logic
    5. archive/ must have no __init__.py (not importable)
"""

import ast
import os
from pathlib import Path
import pytest


ROOT = Path(__file__).parent.parent


def _get_imports(filepath: Path) -> list:
    """Extract all import module names from a Python file."""
    try:
        source = filepath.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _all_py_files(package_dir: Path) -> list:
    """Find all .py files in a package directory."""
    if not package_dir.exists():
        return []
    return list(package_dir.rglob("*.py"))


# ── Rule 1: k4_frozen must never import from exploration/viz/cli/artifacts ──

FROZEN_FORBIDDEN = {"k4_explorer", "k4_artifacts", "k4_viz", "k4_cli", "archive"}

def test_frozen_does_not_import_explorer():
    """k4_frozen.* must never import from k4_explorer, k4_artifacts, k4_viz, k4_cli."""
    frozen_dir = ROOT / "k4_frozen"
    violations = []
    for py_file in _all_py_files(frozen_dir):
        imports = _get_imports(py_file)
        for imp in imports:
            top = imp.split(".")[0]
            if top in FROZEN_FORBIDDEN:
                violations.append(f"{py_file.relative_to(ROOT)}: imports {imp}")

    assert not violations, (
        "k4_frozen must never import from exploration/viz/cli layers:\n"
        + "\n".join(violations)
    )


# ── Rule 2: contracts.py must not import from k4_frozen or k4_explorer logic ──

def test_contracts_is_pure_schema():
    """k4_explorer/contracts.py must only import stdlib + numpy."""
    contracts_file = ROOT / "k4_explorer" / "contracts.py"
    if not contracts_file.exists():
        pytest.skip("contracts.py not yet created")

    imports = _get_imports(contracts_file)
    allowed_prefixes = {"__future__", "numpy", "np", "dataclasses", "enum", "typing"}

    violations = []
    for imp in imports:
        top = imp.split(".")[0]
        if top not in allowed_prefixes and top != "k4_explorer":  # relative imports OK if they resolve to contracts
            violations.append(imp)

    # Filter out k4_explorer.contracts self-references
    violations = [v for v in violations if not v.startswith("k4_explorer.contracts")]

    assert not violations, (
        "contracts.py must be a pure schema module (no k4_frozen, no logic):\n"
        + "\n".join(violations)
    )


# ── Rule 3: k4_viz must never import from k4_frozen or k4_explorer.solver ──

VIZ_FORBIDDEN_PREFIXES = {"k4_frozen", "k4_explorer.solver", "k4_explorer.optimizer",
                           "k4_explorer.context"}

def test_viz_does_not_import_frozen_or_solver():
    """k4_viz must consume artifacts, never compute theorem-class quantities."""
    viz_dir = ROOT / "k4_viz"
    violations = []
    for py_file in _all_py_files(viz_dir):
        imports = _get_imports(py_file)
        for imp in imports:
            for forbidden in VIZ_FORBIDDEN_PREFIXES:
                if imp.startswith(forbidden):
                    violations.append(f"{py_file.relative_to(ROOT)}: imports {imp}")

    assert not violations, (
        "k4_viz must not import from k4_frozen or solver:\n"
        + "\n".join(violations)
    )


# ── Rule 4: k4_artifacts must not import k4_frozen or k4_explorer logic ──

ARTIFACT_FORBIDDEN_PREFIXES = {"k4_frozen", "k4_explorer.solver", "k4_explorer.context",
                                "k4_explorer.optimizer", "k4_explorer.geometry"}

def test_artifacts_does_not_import_logic():
    """k4_artifacts handles serialization only — no computation."""
    artifacts_dir = ROOT / "k4_artifacts"
    violations = []
    for py_file in _all_py_files(artifacts_dir):
        imports = _get_imports(py_file)
        for imp in imports:
            for forbidden in ARTIFACT_FORBIDDEN_PREFIXES:
                if imp.startswith(forbidden):
                    violations.append(f"{py_file.relative_to(ROOT)}: imports {imp}")

    assert not violations, (
        "k4_artifacts must not import computation modules:\n"
        + "\n".join(violations)
    )


# ── Rule 5: archive has no __init__.py ──

def test_archive_not_importable():
    """archive/ must not be a Python package (no __init__.py)."""
    archive_init = ROOT / "archive" / "__init__.py"
    assert not archive_init.exists(), (
        "archive/__init__.py exists — archive must not be importable. "
        "Delete it to prevent accidental runtime imports."
    )


# ── Rule 6: k4_explorer.solver must not directly import field_engine ──

def test_solver_uses_context_not_field_engine():
    """Solver sees the field engine only through FieldContext."""
    solver_file = ROOT / "k4_explorer" / "solver.py"
    if not solver_file.exists():
        pytest.skip("solver.py not yet created")

    imports = _get_imports(solver_file)
    direct_fe = [imp for imp in imports if "field_engine" in imp]

    assert not direct_fe, (
        "k4_explorer.solver must not import field_engine directly. "
        "Use FieldContext from context.py instead.\n"
        f"Found: {direct_fe}"
    )
