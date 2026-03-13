"""
k4_frozen — Immutable K4 Tetrahedral EM Framework Core (v3.0)
==============================================================

Split from K4_FROZEN_V3_COMPLETE.txt. 182/182 consistency checks.
Do NOT edit these files. The only permissible change is bumping
__version__ if a verified correction is applied (with full diff trail).

Layer Architecture:
  LAYER 0:   Integer Matrices (unconditional)       → truth_kernel.py
  LAYER 1:   Graph Theory (geometry-independent)     → truth_kernel.py
  LAYER 1.7: Sign matrix S, Gram⁻¹                  → truth_kernel.py
  LAYER 3-4: EM (Biot-Savart + centroid)             → field_engine.py
  LAYER 4W:  Full-wave (retarded kernel, Z(ω))       → full_wave.py
  LAYER S4:  S₄ rep theory, commutant, ζ₄           → commutant.py
  LAYER 5:   Bose-Mesner algebra {αI+βJ}            → bose_mesner.py
  LAYER 6:   Spherical harmonics                     → spherical_harmonics.py
  LAYER 7:   Sphere sculpting                        → sphere_sculpt.py
  NULL:      Dark lines, isotropy                    → null_tetrahedron.py
  CONTROL:   Ring-quiet mode                         → ring_quiet.py
  SESSION:   Schema + compiler + regression          → session_*.py
  POLICY:    Governance, drift prevention            → policy.py
  INDUCTANCE: Neumann integrals, functional control  → inductance.py

IMPORT RULES:
    This package may import: numpy, scipy, sympy, typing, other k4_frozen modules.
    This package must NEVER import: k4_explorer, k4_artifacts, k4_viz, k4_cli.

Verification: python -m k4_frozen.verify_all
"""

__version__ = "3.0.0"
__frozen_from__ = "K4 Definitive Reference v1.2.0 + Sessions through 2026-03-08"

# ═══════════════════════════════════════════════════════════════════
# Re-export the frozen API
# ═══════════════════════════════════════════════════════════════════

try:
    # Layer 0–1.7: Truth kernel
    from .truth_kernel import (
        M, G, D, B_face, D_red,
        SIGNS, DELTA, C_INT, SIGMA,
        S, GRAM_INV_ALPHA, GRAM_INV_BETA, get_gram_inverse,
        EDGE_LABELS, VERTEX_LABELS, FACE_LABELS, EDGE_INDEX, OPPOSITE_EDGES,
        verify_layer1, verify_sympy,
        get_projectors_exact, decompose_current,
        vertex_injection, face_circulation,
    )

    # Layer 3–4: Field engine
    from .field_engine import (
        MU0, DEFAULT_L,
        make_vertices, make_edges, centroid, face_centers, edge_midpoints,
        biot_savart_segment, field_matrix, field_at_centroid,
        verify_layer4, verify_e_field,
        e_field_volume_matrix,
        centroid_inversion, compute_field,
    )

    # Null analysis
    from .null_tetrahedron import (
        null_tetrahedron_analysis,
    )

    # Session schema
    from .session_schema import (
        ConfigID as FrozenConfigID, BModelTier, ClaimClass as FrozenClaimClass,
    )

    _POPULATED = True

except ImportError as e:
    _POPULATED = False
    _IMPORT_ERROR = str(e)


def check_populated():
    """Verify that the frozen package has been populated with v3 modules."""
    if not _POPULATED:
        raise RuntimeError(
            f"k4_frozen is not fully importable: {_IMPORT_ERROR}\n"
            "Ensure all 17 module files from K4_FROZEN_V3_COMPLETE.txt "
            "are present in k4_frozen/."
        )
