# K4 Field Sculpting Engine

An open exploration engine for tetrahedral electromagnetic field control,
mapping, and sculpting.

Built on a frozen algebraic core — 40+ identities proven to exact
Integer(0) via SymPy — with a numerical field engine, structured
experiment pipeline, and reproducible artifact system.

## What works today

- **Frozen core**: 182 internal consistency checks pass (k4_frozen v3.0)
- **Vertical slice**: `k4 run basic-bz` produces a complete artifact bundle
  with field solve, 9-viewport observable evaluation, and full provenance
- **Import enforcement**: 6 architectural rules verified by test suite
- **18/18 tests passing**

```
$ k4 run basic-bz
Verifying frozen core... OK
Building field context... OK (F0G_residual=0.00e+00, κ=2.000, ceiling=[G])
Solving... OK (I_max=765.466 mA, P=5013.38 µW)
Evaluating viewports... OK (9 viewports)
Artifact saved: runs/2026-03-13_basic_bz_253b8294
```

## What this is

A research and engineering tool for exploring electromagnetic field
control using the K4 complete-graph tetrahedral geometry. The framework
decomposes edge currents into orthogonal cycle and cut subspaces via
exact Hodge decomposition, enabling independent control of internal
fields (centroid B, interior E) and external radiation (far-field
dipole steering).

Core capabilities:
- Exact centroid field inversion (B target → edge currents, machine precision)
- Cycle/cut decomposition with structural orthogonality (proven to Integer(0))
- Null placement at arbitrary interior points
- 9 canonical viewports with selectivity tracking
- Reproducible artifact bundles with claim provenance

## What this is NOT

- Not a medical device, not medical advice, not a treatment protocol
- Not a finished product — this is an active research engine
- Not independently validated against physical measurement (yet)

See [SAFETY.md](SAFETY.md) for the full research-use notice.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v              # 18 tests, all should pass
k4 run basic-bz        # produce first artifact
k4 inspect runs/*/     # inspect the result
```

## Repository structure

```
k4_frozen/       Immutable algebraic core (182 checks, never edit)
k4_explorer/     Exploration engine: geometry adapters, solver, observables
k4_artifacts/    Artifact serialization, provenance, loading
k4_viz/          Visualization (stub — Phase 6)
k4_cli/          Command-line interface
tests/           Import enforcement + vertical slice regression
docs/            Architecture, contracts, theory boundaries
archive/         Legacy material (read-only, never imported)
runs/            Generated experiment artifacts
```

## Architecture

The engine enforces strict layer separation:

- **Layer A** (k4_frozen): Immutable theorem kernel. Integer matrices,
  SymPy proofs, Hodge projectors. Never modified at runtime.
- **Layer B** (k4_frozen): Field engine. Biot-Savart, centroid inversion,
  E-field model. Model-dependent but verified.
- **Layer C** (k4_explorer): Exploration engine. Geometry adapters,
  solver, observables, experiments. Imports from frozen, never the reverse.
- **Layer D** (k4_viz): Visualization. Consumes artifacts. Never computes
  theorem-class quantities.

Every result carries a claim class:
[A] algebraic exact, [G] geometry-dependent exact, [G\*] model-limited,
[M] numerical, [H] heuristic, [C] conjectural.

See [docs/CONSTITUTION.md](docs/CONSTITUTION.md) for the full architecture.

## Licensing

**Software**: Apache License 2.0 — see [LICENSE](LICENSE)

**Hardware/design files**: CERN Open Hardware Licence v2, Weakly
Reciprocal — see [LICENSE-HARDWARE](LICENSE-HARDWARE)

## Patent note

A provisional patent application has been filed. This repo is shared
openly to accelerate research and public benefit. See
[PATENTS.md](PATENTS.md) for details.

## Status and roadmap

| Phase | Status |
|-------|--------|
| Repo scaffold + contracts | ✅ Complete |
| Minimum vertical slice | ✅ Complete |
| Artifact system | ✅ Complete |
| Regression anchors | 🔄 In progress |
| Field sculpting objectives | ⬜ Phase 4 |
| Optimization / inverse design | ⬜ Phase 5 |
| Visualization / shareable demos | ⬜ Phase 6 |

## Attribution

Original project direction and architecture: Alex Ward

Please preserve attribution and provenance metadata in derivative work.
