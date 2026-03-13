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
- Phase 1 complete: scaffold + contracts + vertical slice
- Phase 2 complete: regression pinned, artifacts hardened, 3 figures per run, physical realization layer (62/62 tests)
- Phase 3: website scaffold in web/ (Next.js static export → k4forge.org)
- k4_frozen/ has 182 consistency checks (run with `python -m k4_frozen.verify_all`)

## Import rules (enforced by tests/test_imports.py)
- k4_frozen must never import from k4_explorer
- k4_cli must never import k4_frozen directly — use k4_explorer.runtime facade
- k4_viz must never import from k4_frozen (reads artifacts only)
- k4_explorer.solver must not import k4_frozen.field_engine directly (use context.py)
- k4_explorer.contracts imports only numpy/typing/dataclasses/enum — no logic
- archive/ has no __init__.py — never importable

## Key corrections (must not regress)
- Viewport v0_dir: V[0] - c (centroid toward V0), NOT c - V[0]
- VP-07/VP-08 use C3 axis (v0_hat), NOT hardcoded [1,0,0]; VP-09 stays off-axis
- Centroid inversion: use direct solve (F0M)^-1, NOT closed-form with wrong coefficient
- Vertex stars fail at centroid (NOT face triangles — face triangles span R³ with κ=2)
- E-field mutual angle is 109.5° (NOT 70.5°)
- Each config has its OWN transverse plane for AC orbits (NOT universal [1,1,1])
- F₀·G=0 requires T_d symmetry only (NOT Biot-Savart specifically)

## Test commands
```bash
pytest tests/ -v                    # all 62 tests
pytest tests/test_imports.py -v     # import rule enforcement (8 tests)
pytest tests/test_regression.py -v  # I_edge regression + reproducibility
pytest tests/test_artifacts.py -v   # artifact round-trip + inspect
pytest tests/test_figures.py -v     # figure generation + artifact integration
pytest tests/test_realization.py -v # physical realization tests (20 tests)
python -m k4_cli.run run basic-bz   # end-to-end with figures
python -m k4_cli.run figures <dir>  # regenerate figures from artifact
```

## Website (web/)
- Next.js App Router with static export (`output: "export"`)
- Routes: /, /about, /demo, /docs, /safety, /updates, /contact
- Demo page consumes precomputed artifacts from public/demo/
- No live solving — everything precomputed with full provenance
- Deploy: `cd web && npm run build` → rsync `out/` to droplet behind Caddy
- Export artifact: `npx tsx scripts/export-artifact.ts <artifact-dir> <preset-id>`
