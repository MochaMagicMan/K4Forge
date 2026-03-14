"""
k4_theory — Standalone K4 Theory Mining & Verification Engine
=============================================================

Parallel to k4_frozen: a self-contained proof chain, symmetry miner,
and candidate discovery system.  Does NOT import from k4_frozen.

Contains its own exact algebraic kernel (SymPy), symbolic Biot-Savart,
and numerical engine.  This is intentional: k4_theory serves as an
independent verification oracle that can cross-check k4_frozen results
without sharing code paths.

Usage:
    from k4_theory.theory_miner import run_proofs, run_mining, run_all
    results = run_proofs()

    # Or from CLI:
    python -m k4_theory.theory_miner --prove
    python -m k4_theory.theory_miner --mine
    python -m k4_theory.theory_miner --discover
    python -m k4_theory.theory_miner          # all phases

IMPORT RULES:
    This package may import: numpy, sympy, stdlib.
    This package must NEVER import: k4_frozen, k4_explorer, k4_artifacts, k4_viz, k4_cli.
    (Self-contained by design — independent verification oracle.)
"""

__version__ = "1.0.0"

from .theory_miner import (
    THEOREM_REGISTRY,
    run_proofs,
    run_mining,
    run_discover,
    run_all,
)
