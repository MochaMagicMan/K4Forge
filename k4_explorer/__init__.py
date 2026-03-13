"""
k4_explorer — K4 Exploration Engine
=====================================

The exploration layer. Imports from k4_frozen (never the reverse).
Produces typed data objects from contracts.py.

IMPORT RULES:
    May import: k4_frozen.*, k4_explorer.contracts, numpy, scipy
    Must never import: k4_artifacts, k4_viz, k4_cli, archive
"""

__version__ = "0.1.0"
