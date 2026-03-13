"""
k4_viz.figures — Run Figure Generation
========================================

Generates the three standard figures for every K4 run artifact:

    1. geometry.png       — 3D tetrahedron, clean, large
    2. field_slice.png    — |B| heatmap in z=0 plane
    3. probe_summary.png  — viewport bar chart

IMPORT RULES:
    May import: k4_explorer.contracts, matplotlib, numpy
    Must NEVER import: k4_frozen, k4_explorer.solver, k4_explorer.context

All geometry data arrives as plain arrays (V, L, I_edge, etc.),
passed by the caller (k4_cli.run). This module never builds a
FieldContext or calls field_engine.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (needed for 3D projection)
from pathlib import Path
from typing import Callable, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════
# STANDARD FORMATTING
# ═══════════════════════════════════════════════════════════════════

# Canonical edge ordering: (0,1), (0,2), (0,3), (1,2), (1,3), (2,3)
EDGE_PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
EDGE_LABELS = ("E01", "E02", "E03", "E12", "E13", "E23")
VERTEX_LABELS = ("V0", "V1", "V2", "V3")

# Viewport marker colors by panel family
VP_COLORS = {
    "VP-01": "gold",       # centroid
    "VP-02": "#1565c0",    # certification
    "VP-03": "#1565c0",    # certification
    "VP-04": "#2e7d32",    # cut characterization
    "VP-05": "#e65100",    # stress
    "VP-06": "#e65100",    # stress
    "VP-07": "#2e7d32",    # cut characterization
    "VP-08": "#2e7d32",    # cut characterization
    "VP-09": "#7b1fa2",    # null orbit
}

# Dark theme colors
BG_COLOR = '#0a0a0f'
SURFACE_COLOR = '#12121a'
TEXT_COLOR = '#e8e8f0'
MUTED_COLOR = '#8888a0'
ACCENT_COLOR = '#4488ff'
EDGE_COLOR = '#6688cc'
VERTEX_COLOR = '#ff6666'
CENTROID_COLOR = '#ffd700'
GRID_COLOR = '#222233'


def _stamp(ax, claim: str, model: str, extra: str = ""):
    """Add claim class + model stamp to bottom-left of figure."""
    text = f"[{claim}] {model}"
    if extra:
        text += f" | {extra}"
    fig = ax.get_figure()
    fig.text(0.02, 0.02, text,
             fontsize=7, color=MUTED_COLOR, family='monospace',
             verticalalignment='bottom')


def _save(fig, name: str, output_dir: str) -> str:
    """Save figure as PNG and return path."""
    path = str(Path(output_dir) / f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    return path


def _dark_style_ax(ax, is_3d=False):
    """Apply dark theme to an axes."""
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=MUTED_COLOR, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.xaxis.label.set_color(MUTED_COLOR)
    ax.yaxis.label.set_color(MUTED_COLOR)
    if is_3d:
        ax.zaxis.label.set_color(MUTED_COLOR)
        ax.zaxis.set_tick_params(colors=MUTED_COLOR)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor(GRID_COLOR)
        ax.yaxis.pane.set_edgecolor(GRID_COLOR)
        ax.zaxis.pane.set_edgecolor(GRID_COLOR)
        ax.grid(False)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 1: GEOMETRY — clean tetrahedron, no grid clutter
# ═══════════════════════════════════════════════════════════════════

def plot_geometry(V: np.ndarray, L: float, output_dir: str,
                  observables: Optional[list] = None) -> str:
    """
    3D wireframe of the regular tetrahedron — large, clean, minimal.
    No grid, no face centers, just the structure.
    """
    fig = plt.figure(figsize=(9, 8), facecolor=BG_COLOR)
    ax = fig.add_subplot(111, projection='3d')
    _dark_style_ax(ax, is_3d=True)

    # Draw edges — thick, glowing
    for idx, (i, j) in enumerate(EDGE_PAIRS):
        ax.plot(*zip(V[i], V[j]), color=EDGE_COLOR, linewidth=2.5, alpha=0.9)

    # Draw vertices — prominent
    for i, v in enumerate(V):
        ax.scatter(v[0], v[1], v[2], s=120, c=VERTEX_COLOR, zorder=5,
                   edgecolors='white', linewidths=0.5)
        # Push label outward from centroid
        c = V.mean(axis=0)
        direction = v - c
        direction = direction / np.linalg.norm(direction) * L * 0.15
        lpos = v + direction
        ax.text(lpos[0], lpos[1], lpos[2], VERTEX_LABELS[i],
                fontsize=11, fontweight='bold', color=VERTEX_COLOR)

    # Draw centroid — gold star
    c = V.mean(axis=0)
    ax.scatter(c[0], c[1], c[2], s=150, c=CENTROID_COLOR, marker='*',
               zorder=6, edgecolors='white', linewidths=0.5)

    # Camera angle for clear depth
    ax.view_init(elev=20, azim=-55)

    # Remove axis clutter — let the tetrahedron speak
    ax.set_axis_off()

    # Title
    ax.set_title(f'Regular K4 Tetrahedron\nL = {L * 100:.1f} cm  ·  Edge-filament model',
                 fontsize=13, color=TEXT_COLOR, pad=10)
    _stamp(ax, 'G', f'Regular K4, L = {L * 100:.1f} cm')

    return _save(fig, 'geometry', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 2: FIELD SLICE — |B| in z=0 plane, clean orientation
# ═══════════════════════════════════════════════════════════════════

def plot_field_slice(V: np.ndarray, I_edge: np.ndarray, L: float,
                     field_eval: Callable, output_dir: str,
                     n_grid: int = 30, z_plane: float = 0.0) -> str:
    """
    2D heatmap of |B| with quiver arrows in the z=0 plane.
    Dark theme, cleaner overlays, better orientation.
    """
    extent = 2.0 * L
    x = np.linspace(-extent, extent, n_grid)
    y = np.linspace(-extent, extent, n_grid)
    X, Y = np.meshgrid(x, y)
    Bmag = np.zeros_like(X)
    Bx_grid = np.zeros_like(X)
    By_grid = np.zeros_like(X)

    for i in range(n_grid):
        for j in range(n_grid):
            r = np.array([X[i, j], Y[i, j], z_plane])
            F = field_eval(r)
            B = F @ I_edge
            Bmag[i, j] = np.linalg.norm(B)
            Bx_grid[i, j] = B[0]
            By_grid[i, j] = B[1]

    fig, ax = plt.subplots(figsize=(9, 8), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Use log scale if dynamic range is large
    vmin = Bmag[Bmag > 0].min() if np.any(Bmag > 0) else 1e-10
    vmax = Bmag.max()
    if vmax / vmin > 100:
        from matplotlib.colors import LogNorm
        im = ax.pcolormesh(X * 1e3, Y * 1e3, Bmag * 1e6,
                           shading='auto', cmap='inferno',
                           norm=LogNorm(vmin=vmin * 1e6, vmax=vmax * 1e6))
    else:
        im = ax.pcolormesh(X * 1e3, Y * 1e3, Bmag * 1e6,
                           shading='auto', cmap='inferno')

    cbar = plt.colorbar(im, ax=ax, label='|B| (µT)', shrink=0.85)
    cbar.ax.yaxis.label.set_color(MUTED_COLOR)
    cbar.ax.tick_params(colors=MUTED_COLOR)

    # Quiver (subsample for clarity)
    step = max(1, n_grid // 10)
    bmax = Bmag.max()
    if bmax > 0:
        ax.quiver(X[::step, ::step] * 1e3, Y[::step, ::step] * 1e3,
                  Bx_grid[::step, ::step], By_grid[::step, ::step],
                  color='white', alpha=0.4, scale_units='inches',
                  scale=bmax * 10)

    # Draw edge projections onto z=0 — thin, subtle
    for i, j in EDGE_PAIRS:
        ax.plot([V[i][0] * 1e3, V[j][0] * 1e3],
                [V[i][1] * 1e3, V[j][1] * 1e3],
                color=EDGE_COLOR, linewidth=1.0, alpha=0.5)

    # Mark projected vertices
    for i, v in enumerate(V):
        ax.plot(v[0] * 1e3, v[1] * 1e3, 's', color=VERTEX_COLOR,
                markersize=6, markeredgecolor='white', markeredgewidth=0.5)

    # Mark centroid
    ax.plot(0, 0, '*', color=CENTROID_COLOR, markersize=14,
            markeredgecolor='white', markeredgewidth=0.5)

    ax.set_xlabel('X (mm)', color=MUTED_COLOR)
    ax.set_ylabel('Y (mm)', color=MUTED_COLOR)
    ax.tick_params(colors=MUTED_COLOR)
    ax.set_title(f'|B| Field Magnitude  ·  XY plane at z = {z_plane * 1e3:.1f} mm\n'
                 f'Biot-Savart thin-wire  ·  Solved edge currents',
                 fontsize=12, color=TEXT_COLOR, pad=10)

    # Plane label inset
    fig.text(0.98, 0.02, f'Slice: z = {z_plane * 1e3:.1f} mm  |  Normal: +Z',
             fontsize=8, color=MUTED_COLOR, family='monospace',
             ha='right', va='bottom')

    _stamp(ax, 'M', f'Biot-Savart, z={z_plane}m slice')

    return _save(fig, 'field_slice', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 3: PROBE SUMMARY — viewport comparison
# ═══════════════════════════════════════════════════════════════════

def plot_probe_summary(observables: list, output_dir: str) -> str:
    """
    Horizontal bar chart of |B| across all viewports with claim classes.
    Dark theme.
    """
    entries = []
    for o in observables:
        if hasattr(o, 'viewport_id'):
            entries.append({
                'viewport_id': o.viewport_id,
                'B_magnitude': o.B_magnitude,
                'B_total': o.B_total if isinstance(o.B_total, list) else o.B_total.tolist(),
                'selectivity': o.selectivity,
                'claim_class': o.claim_class.value if hasattr(o.claim_class, 'value') else o.claim_class,
            })
        else:
            entries.append(o)

    entries.sort(key=lambda e: e.get('viewport_id', ''))

    vp_ids = [e['viewport_id'] for e in entries]
    B_mags = [e['B_magnitude'] * 1e6 for e in entries]
    claims = [e.get('claim_class', 'M') for e in entries]

    claim_colors = {
        'A': '#1b5e20', 'G': '#ffd700', 'G*': '#558b2f',
        'M': '#4488ff', 'H': '#f57f17', 'C': '#bf360c',
    }
    colors = [claim_colors.get(c, '#757575') for c in claims]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=MUTED_COLOR)

    y_pos = np.arange(len(vp_ids))
    ax.barh(y_pos, B_mags, color=colors, edgecolor='none', alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(vp_ids, fontsize=10, color=TEXT_COLOR, family='monospace')
    ax.set_xlabel('|B| (µT)', color=MUTED_COLOR)
    ax.set_title('Probe Comparison\nGold = [G] geometry-exact   Blue = [M] model-dependent',
                 fontsize=12, color=TEXT_COLOR)
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.15, color=GRID_COLOR)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    # Annotate with magnitude and claim
    max_b = max(B_mags) if B_mags else 1.0
    for i, e in enumerate(entries):
        label = f" {B_mags[i]:.3f} µT  [{claims[i]}]"
        ax.text(B_mags[i] + max_b * 0.02, i, label,
                va='center', fontsize=8, family='monospace', color=TEXT_COLOR)

    fig.tight_layout()
    return _save(fig, 'probe_summary', output_dir)


# ═══════════════════════════════════════════════════════════════════
# MASTER: Generate all run figures
# ═══════════════════════════════════════════════════════════════════

def generate_run_figures(V: np.ndarray, L: float, I_edge: np.ndarray,
                         observables: list, field_eval: Callable,
                         output_dir: str) -> Dict[str, str]:
    """
    Generate the standard three-figure set for a run.

    Returns:
        dict of {figure_name: file_path}
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    figures = {}
    figures['geometry'] = plot_geometry(V, L, output_dir, observables=observables)
    figures['field_slice'] = plot_field_slice(V, I_edge, L, field_eval, output_dir)
    figures['probe_summary'] = plot_probe_summary(observables, output_dir)

    return figures
