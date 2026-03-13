# Mining Notes

This directory contains archived code that is READ-ONLY.
It has no __init__.py and must NEVER be imported at runtime.

## What was extracted and where it went

| Source | Extracted | Destination |
|--------|-----------|-------------|
| k4_engine.py signal layer | 27-param SignalState | k4_explorer/drive.py |
| k4_engine.py modes | 12 operating modes | k4_explorer/trajectory.py |
| k4_engine.py viewports | 9 canonical viewports | k4_explorer/observables.py |
| k4_engine.py SVD analysis | Trajectory dimensionality | k4_explorer/trajectory.py |
| k4_engine.py session compiler | Tier system, regression | k4_explorer/experiment.py |
| session_compiler_v3.py | DC solve, 12 regression tests | k4_explorer/solver.py |
