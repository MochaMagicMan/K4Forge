"""
k4_explorer.presets — Canonical Presets
========================================

Pre-loaded ControlSpec + GeometrySpec pairs for common scenarios.
These are regression anchors. If a preset's output changes, investigate.

IMPORT RULES:
    May import: k4_explorer.contracts, k4_explorer.geometry
    Must never import: k4_explorer.solver, k4_frozen
"""

from .contracts import ControlSpec, ConfigID
from .geometry import adapt_regular

# Default geometry: regular K4, L = 0.1m, Config D
DEFAULT_L = 0.1
DEFAULT_WIRE_RADIUS = 5e-4  # 0.5mm


def BASIC_BZ():
    """Baseline: B = [0, 0, 10µT], E = [100, 0, 0] V/m, DC."""
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 10e-6),
            E_target=(100.0, 0.0, 0.0),
        ),
        adapt_regular(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def NULL_CENTER():
    """B + E + null at centroid. Cheapest null (u_coil ≈ 0)."""
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 10e-6),
            E_target=(100.0, 0.0, 0.0),
            null_point=(0.0, 0.0, 0.0),  # centroid null is free
        ),
        adapt_regular(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def NULL_ORBIT():
    """B + E + null at 0.1L off-center. THE benchmark."""
    L = DEFAULT_L
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 10e-6),
            E_target=(100.0, 0.0, 0.0),
            null_point=(0.1 * L, 0.0, 0.0),
        ),
        adapt_regular(L=L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def CUT_REACH():
    """Cut-coil only, cycle off. Shows monopole-like far field."""
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 0.0),  # zero centroid B (cycle = 0)
            E_target=(100.0, 0.0, 0.0),
        ),
        adapt_regular(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def B_DIAGONAL():
    """B along [1,1,1] diagonal. Tests isotropic cost at centroid."""
    import numpy as np
    B_mag = 10e-6
    d = B_mag / np.sqrt(3)
    return (
        ControlSpec(
            B_target=(d, d, d),
            E_target=(0.0, 0.0, 0.0),
        ),
        adapt_regular(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def MAX_STRESS():
    """Large currents. Stress panel demo."""
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 100e-6),  # 100 µT — 10× baseline
            E_target=(1000.0, 0.0, 0.0),
        ),
        adapt_regular(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


def OVER_CONSTRAINED():
    """B + E + null + probe. Tier 3 — shows graceful degradation."""
    from .contracts import ProbeTarget
    L = DEFAULT_L
    return (
        ControlSpec(
            B_target=(0.0, 0.0, 10e-6),
            E_target=(100.0, 0.0, 0.0),
            null_point=(0.1 * L, 0.0, 0.0),
            probe_targets=(
                ProbeTarget(
                    position=(0.0, 0.05 * L, 0.0),
                    B_target=(5e-6, 0.0, 0.0),
                    priority="SOFT",
                ),
            ),
        ),
        adapt_regular(L=L, wire_radius=DEFAULT_WIRE_RADIUS),
    )


# Registry for CLI lookup
PRESET_REGISTRY = {
    "basic-bz": BASIC_BZ,
    "null-center": NULL_CENTER,
    "null-orbit": NULL_ORBIT,
    "cut-reach": CUT_REACH,
    "b-diagonal": B_DIAGONAL,
    "max-stress": MAX_STRESS,
    "over-constrained": OVER_CONSTRAINED,
}
