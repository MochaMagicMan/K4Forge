# CLAUDE.md

This is the K4 Tetrahedral EM Field Control exploration engine.

## Rules
- Never edit files in k4_frozen/ — that's the immutable algebraic core
- Never duplicate frozen matrices — import from k4_frozen
- Every result must carry a ClaimRecord with claim class [A]/[G]/[G*]/[M]/[H]/[C]
- Run `python -m pytest tests/ -v` after every change
- See docs/CONSTITUTION.md for full architecture
- See docs/IMPLEMENTATION_DESIGN.md for build plan

## Claim taxonomy
- [A] Algebraic exact — Integer(0) via SymPy, unconditional
- [G] Geometry-dependent exact — requires regular K4 + named model
- [G*] Model-limited — valid within stated regime only
- [M] Numerical — not a proof, never promote without named proof path
- [H] Heuristic — engineering guidance
- [C] Conjectural — incomplete proof

## Current state
- Phase 1 complete: scaffold + contracts + vertical slice (18/18 tests)
- Phase 2 next: regression values for viewports, observable verification
- k4_frozen/ has 182 consistency checks (run with `python -m k4_frozen.verify_all`)

## Import rules (enforced by tests/test_imports.py)
- k4_frozen must never import from k4_explorer
- k4_viz must never import from k4_frozen (reads artifacts only)
- k4_explorer.solver must not import k4_frozen.field_engine directly (use context.py)
- k4_explorer.contracts imports only numpy/typing/dataclasses/enum — no logic
- archive/ has no __init__.py — never importable

## Key corrections (must not regress)
- Centroid inversion: use direct solve (F0M)^-1, NOT closed-form with wrong coefficient
- Vertex stars fail at centroid (NOT face triangles — face triangles span R³ with κ=2)
- E-field mutual angle is 109.5° (NOT 70.5°)
- Each config has its OWN transverse plane for AC orbits (NOT universal [1,1,1])
- F₀·G=0 requires T_d symmetry only (NOT Biot-Savart specifically)

## Test commands
```bash
pytest tests/ -v                    # all 18 tests
pytest tests/test_imports.py -v     # import rule enforcement only
python -m k4_cli.run run basic-bz   # end-to-end vertical slice
```
