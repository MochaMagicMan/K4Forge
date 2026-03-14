"""
tests/test_theory_miner.py — Integration Tests for k4_theory
=============================================================

Verifies that theory_miner integrates cleanly into K4Forge:
  1. Imports without touching k4_frozen
  2. Proof chain runs and passes
  3. Expected theorem count and key upgrades present
  4. Symmetry mining produces expected identity count
  5. Integer field-structure matrices match k4_frozen's truth_kernel
  6. No existing tests regress (verified by running full suite)

These tests do NOT modify k4_frozen.  k4_theory is a parallel
verification oracle.
"""

import pytest
import numpy as np


# ── Basic import ──

def test_theory_miner_imports():
    """k4_theory.theory_miner imports without error."""
    from k4_theory import theory_miner
    assert hasattr(theory_miner, 'THEOREM_REGISTRY')
    assert hasattr(theory_miner, 'run_proofs')
    assert hasattr(theory_miner, 'run_mining')


def test_theory_miner_is_self_contained():
    """k4_theory must not import from k4_frozen or k4_explorer."""
    import ast
    from pathlib import Path

    theory_dir = Path(__file__).parent.parent / "k4_theory"
    forbidden = {"k4_frozen", "k4_explorer", "k4_artifacts", "k4_viz", "k4_cli"}
    violations = []

    for py_file in theory_dir.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden:
                        violations.append(f"{py_file.name}: imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in forbidden:
                    violations.append(f"{py_file.name}: from {node.module}")

    assert not violations, (
        "k4_theory must be self-contained (no k4_frozen imports):\n"
        + "\n".join(violations)
    )


# ── Theorem registry ──

def test_theorem_count():
    """At least 46 theorems registered."""
    from k4_theory.theory_miner import THEOREM_REGISTRY
    assert len(THEOREM_REGISTRY) >= 46, (
        f"Expected >= 46 theorems, got {len(THEOREM_REGISTRY)}"
    )


def test_integer_field_theorems_present():
    """Key INT.* theorems (from K4Forge truth_kernel merge) are registered."""
    from k4_theory.theory_miner import THEOREM_REGISTRY
    required = [
        "INT.CG_zero",      # Cut annihilation at T0
        "INT.det_CM_32",     # Controllability at T0
        "INT.gram_CM",       # kappa=2 at T0
        "INT.STS_gram",      # S^T S = Gram
        "INT.isotropy",      # Centroid isotropy
        "INT.CM_eq_neg2S",   # C_INT*M = -2*S
    ]
    for thm_id in required:
        assert thm_id in THEOREM_REGISTRY, f"Missing theorem: {thm_id}"


def test_multipole_theorems_present():
    """Selection rules from k4lab_v5 are registered."""
    from k4_theory.theory_miner import THEOREM_REGISTRY
    for sel in ["Sel.1", "Sel.2", "Sel.3"]:
        assert sel in THEOREM_REGISTRY, f"Missing selection rule: {sel}"


def test_inductance_theorems_present():
    """T2.5-T2.7 inductance theorems are registered."""
    from k4_theory.theory_miner import THEOREM_REGISTRY
    for tid in ["T2.5", "T2.6", "T2.7"]:
        assert tid in THEOREM_REGISTRY, f"Missing inductance theorem: {tid}"


# ── Proof execution (fast subset) ──

def test_integer_proofs_pass():
    """All T0.* and INT.* proofs pass (pure integer, < 1s total)."""
    from k4_theory.theory_miner import THEOREM_REGISTRY

    failures = []
    for thm_id, rec in THEOREM_REGISTRY.items():
        if thm_id.startswith(("T0.", "INT.")):
            try:
                ok = rec.prove()
            except Exception as e:
                ok = False
                failures.append(f"{thm_id}: {e}")
                continue
            if not ok:
                failures.append(f"{thm_id}: returned False")

    assert not failures, "Integer proof failures:\n" + "\n".join(failures)


def test_topology_proofs_pass():
    """All T1.* proofs pass."""
    from k4_theory.theory_miner import THEOREM_REGISTRY

    failures = []
    for thm_id, rec in THEOREM_REGISTRY.items():
        if thm_id.startswith("T1."):
            try:
                ok = rec.prove()
            except Exception as e:
                failures.append(f"{thm_id}: {e}")
                continue
            if not ok:
                failures.append(f"{thm_id}: returned False")

    assert not failures, "Topology proof failures:\n" + "\n".join(failures)


def test_em_proofs_pass():
    """T3.* and T2.* proofs pass."""
    from k4_theory.theory_miner import THEOREM_REGISTRY

    failures = []
    for thm_id, rec in THEOREM_REGISTRY.items():
        if thm_id.startswith(("T2.", "T3.")):
            try:
                ok = rec.prove()
            except Exception as e:
                failures.append(f"{thm_id}: {e}")
                continue
            if not ok:
                failures.append(f"{thm_id}: returned False")

    assert not failures, "EM proof failures:\n" + "\n".join(failures)


# ── Cross-validation against k4_frozen ──

def test_matrices_match_frozen():
    """theory_miner's integer matrices match k4_frozen.truth_kernel."""
    from k4_theory.theory_miner import exact_M, exact_G, exact_D, exact_C_INT, exact_S_SIGN
    from k4_frozen.truth_kernel import M, G, D, C_INT, S

    # Convert SymPy to numpy for comparison
    tm_M = np.array(exact_M().tolist(), dtype=np.int64)
    tm_G = np.array(exact_G().tolist(), dtype=np.int64)
    tm_D = np.array(exact_D().tolist(), dtype=np.int64)
    tm_C = np.array(exact_C_INT().tolist(), dtype=np.int64)
    tm_S = np.array(exact_S_SIGN().tolist(), dtype=np.int64)

    assert np.array_equal(tm_M, M), "M matrices differ"
    assert np.array_equal(tm_G, G), "G matrices differ"
    assert np.array_equal(tm_D, D), "D matrices differ"
    assert np.array_equal(tm_C, C_INT), "C_INT matrices differ"
    assert np.array_equal(tm_S, S), "S sign matrices differ"


def test_projectors_match_frozen():
    """theory_miner's adjugate-based projectors match k4_frozen."""
    from k4_theory.theory_miner import np_projectors
    from k4_frozen.truth_kernel import get_projectors_exact

    tm_Pc, tm_Pg = np_projectors()
    frozen_Pc, frozen_Pg = get_projectors_exact()

    np.testing.assert_allclose(tm_Pc, frozen_Pc, atol=1e-14,
                               err_msg="Cycle projectors differ")
    np.testing.assert_allclose(tm_Pg, frozen_Pg, atol=1e-14,
                               err_msg="Cut projectors differ")


# ── Mining produces expected results ──

def test_mining_finds_identities():
    """Symmetry miner finds >= 20 identities."""
    from k4_theory.theory_miner import mine_identities
    discoveries = mine_identities(n_spatial=15, extent=2.0, tol=1e-10, verbose=False)
    assert len(discoveries) >= 20, (
        f"Expected >= 20 mined identities, got {len(discoveries)}"
    )


def test_mining_finds_dark_lines():
    """Symmetry miner finds full-null on axis (dark lines)."""
    from k4_theory.theory_miner import mine_identities
    discoveries = mine_identities(n_spatial=15, extent=2.0, tol=1e-10, verbose=False)
    axis_nulls = [d for d in discoveries
                  if d.identity_type == 'full_null' and d.fixed_set == 'axis']
    assert len(axis_nulls) >= 3, (
        f"Expected >= 3 dark-line identities, got {len(axis_nulls)}"
    )
