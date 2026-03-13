# HOW TO APPLY THESE FILES
# ========================
#
# This documents the exact integration steps for Claude Code.
#
# FILES PROVIDED:
#   contracts_additions.py  → append to end of k4_explorer/contracts.py
#   geometry_additions.py   → append to end of k4_explorer/geometry.py
#   context_addition.py     → append to end of k4_explorer/context.py
#   test_realization.py     → drop into tests/test_realization.py
#
# PATCHES TO EXISTING CODE:
#
# ── contracts.py: add edge_lengths to GeometrySpec ──
#
# In the GeometrySpec dataclass (around line 210), add ONE field:
#
#   BEFORE:
#     vertices: np.ndarray
#     edge_length: float
#     symmetry_class: SymmetryClass
#
#   AFTER:
#     vertices: np.ndarray
#     edge_length: float
#     edge_lengths: Optional[np.ndarray] = None  # (6,) per-edge, for non-uniform
#     symmetry_class: SymmetryClass
#
# ── geometry.py: update adapt_irregular to compute edge_lengths ──
#
# In adapt_irregular(), after computing `lengths`, add:
#
#     edge_lengths_arr = np.array(lengths)
#
# And pass it to GeometrySpec:
#
#     return GeometrySpec(
#         vertices=vertices,
#         edge_length=float(mean_L),
#         edge_lengths=edge_lengths_arr,     # ← ADD THIS LINE
#         symmetry_class=sym,
#         ...
#     )
#
# Also update adapt_regular() similarly:
#
#     edge_lengths_arr = np.full(6, L)
#
# ── context.py: add the import ──
#
# At the top of context.py, add to the imports:
#
#     from .contracts import PhysicalRealization, EdgeModel
#
# Then append the build_context_from_realization function from
# context_addition.py.
#
# ── geometry.py: add imports at top ──
#
# Add these imports near the top of geometry.py:
#
#     from .contracts import (
#         GeometrySpec, SymmetryClass, ClaimClass, ConfigID,
#         EdgeModel, EdgeRealization, PhysicalRealization, EDGE_PAIRS,
#     )
#
# Then append everything from geometry_additions.py.
#
# ── VERIFICATION ──
#
# After applying all changes:
#
#   pytest tests/ -v
#
# Expected: all existing tests still pass + new test_realization.py tests pass.
# The critical invariant: build_filament_realization → build_context_from_realization
# must produce IDENTICAL F0 to the existing build_context pipeline.
