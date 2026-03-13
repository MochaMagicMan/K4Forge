"""
k4_explorer.runtime — Frozen Core Facade
==========================================

Thin facade so that k4_cli and other consumers never import k4_frozen
directly. All frozen-core queries go through here.

This is the clean boundary: CLI asks runtime, runtime asks frozen.
"""


def check_frozen():
    """Verify frozen core is populated. Raises RuntimeError if not."""
    from k4_frozen import check_populated
    check_populated()


def frozen_version() -> str:
    """Return the version string of the frozen core."""
    from k4_frozen import __version__
    return __version__


def run_frozen_verification(verbose: bool = True) -> dict:
    """Run the full 182-gate verification suite. Returns report dict."""
    from k4_frozen.verify_all import run_verification
    return run_verification(verbose=verbose)
