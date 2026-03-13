"""
k4_artifacts.digest — Code Provenance
=======================================

Computes SHA-256 digests of source files for reproducibility tracking.
"""

import hashlib
from pathlib import Path
from typing import Dict


def file_digest(path: Path) -> str:
    """SHA-256 hex digest of a single file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()[:16]}"


def solver_digest() -> str:
    """Digest of the solver source — the primary computation code."""
    solver_path = Path(__file__).parent.parent / "k4_explorer" / "solver.py"
    if solver_path.exists():
        return file_digest(solver_path)
    return "sha256:unknown"


def frozen_digest() -> str:
    """Digest of the frozen truth_kernel — the algebraic core."""
    tk_path = Path(__file__).parent.parent / "k4_frozen" / "truth_kernel.py"
    if tk_path.exists():
        return file_digest(tk_path)
    return "sha256:not_populated"


def environment_info() -> Dict[str, str]:
    """Capture runtime environment for reproducibility."""
    import sys
    import platform
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    try:
        import numpy
        info["numpy_version"] = numpy.__version__
    except ImportError:
        pass
    try:
        import scipy
        info["scipy_version"] = scipy.__version__
    except ImportError:
        pass
    try:
        import sympy
        info["sympy_version"] = sympy.__version__
    except ImportError:
        pass
    return info
