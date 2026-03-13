"""
diagnostics.py — Visual Demonstrations of K₄ Theorems
======================================================

This module generates the plots that make the theorems real.
Every function produces a self-contained figure that demonstrates
one specific K₄ property with labeled axes, claim tags, and
model declarations.

No plot is valid without its model stamp.

Dependencies: matplotlib, numpy (both in standard scientific Python)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D
from typing import Optional, Tuple, List, Dict
from pathlib import Path

from . import truth_kernel as tk
from . import field_engine as fe


# ═══════════════════════════════════════════════════════════════════
# STANDARD FIGURE FORMATTING
# ═══════════════════════════════════════════════════════════════════

def _stamp(ax, claim: str, model: str, extra: str = ""):
    """Add claim class + model stamp to bottom-left of axes."""
    text = f"[{claim}] {model}"
    if extra:
        text += f" | {extra}"
    ax.text(0.02, 0.02, text, transform=ax.transAxes,
            fontsize=7, color='gray', family='monospace',
            verticalalignment='bottom')


def _save(fig, name: str, output_dir: str = ".") -> str:
    """Save figure and return path."""
    path = str(Path(output_dir) / f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


# ═══════════════════════════════════════════════════════════════════
# FIGURE 1: THE TETRAHEDRON (geometry + labels)
# ═══════════════════════════════════════════════════════════════════

def plot_tetrahedron(L: float = 0.1, output_dir: str = ".") -> str:
    """
    Plot the regular tetrahedron with labeled vertices, edges, and centroid.
    Shows the physical structure that everything else depends on.
    """
    V = fe.make_vertices(L)
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Draw edges
    pairs = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    for idx, (i, j) in enumerate(pairs):
        ax.plot(*zip(V[i], V[j]), 'b-', linewidth=1.5, alpha=0.7)
        mid = (V[i] + V[j]) / 2
        ax.text(*mid, f' {tk.EDGE_LABELS[idx]}', fontsize=8, color='blue')

    # Draw vertices
    for i, v in enumerate(V):
        ax.scatter(*v, s=80, c='red', zorder=5)
        ax.text(v[0]*1.15, v[1]*1.15, v[2]*1.15,
                f'{tk.VERTEX_LABELS[i]}', fontsize=10, fontweight='bold', color='red')

    # Draw centroid
    c = fe.centroid(V)
    ax.scatter(*c, s=100, c='gold', marker='*', zorder=6, edgecolors='black')
    ax.text(c[0]+L*0.05, c[1], c[2], 'centroid', fontsize=9, color='goldenrod')

    # Draw face centers
    fc = fe.face_centers(V)
    for i, f in enumerate(fc):
        ax.scatter(*f, s=40, c='green', marker='D', zorder=5, alpha=0.7)
        ax.text(f[0]+L*0.03, f[1], f[2], f'F{i}', fontsize=8, color='green')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title(f'Regular K₄ Tetrahedron (L = {L} m)\n'
                 f'4 vertices · 6 edges · 4 faces · centroid at origin',
                 fontsize=11)
    _stamp(ax, 'G', f'regular K₄, L={L}m')

    return _save(fig, 'fig01_tetrahedron', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 2: CUT ANNIHILATION (F₀·G = 0 demonstration)
# ═══════════════════════════════════════════════════════════════════

def plot_cut_annihilation(L: float = 0.1, output_dir: str = ".") -> str:
    """
    Demonstrate T3.1: cut-space currents produce zero B at centroid.
    Shows |B_cut| vs |B_cycle| for random excitations at centroid.
    This is the core selection rule — the reason K₄ works.
    """
    V = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V)
    M_f = tk.M.astype(float)
    G_f = tk.G.astype(float)

    n_samples = 200
    B_cyc_norms = []
    B_cut_norms = []

    rng = np.random.RandomState(42)
    for _ in range(n_samples):
        w = rng.randn(3)
        u = rng.randn(3)
        B_cyc = F0 @ M_f @ w
        B_cut = F0 @ G_f @ u
        B_cyc_norms.append(np.linalg.norm(B_cyc))
        B_cut_norms.append(np.linalg.norm(B_cut))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: histogram comparison
    ax1.hist(B_cyc_norms, bins=30, alpha=0.7, label='|B| from cycle (M·w)', color='steelblue')
    ax1.axvline(0, color='red', linewidth=2, linestyle='--', label='|B| from cut (G·u) — ALL zero')
    ax1.set_xlabel('|B| at centroid (T)')
    ax1.set_ylabel('Count')
    ax1.set_title('T3.1: Cut Annihilation at Centroid\n'
                   '200 random excitations, unit-variance weights')
    ax1.legend(fontsize=9)
    _stamp(ax1, 'G', 'Biot-Savart, centroid')

    # Right: scatter of |B_cycle| vs |B_cut|
    ax2.scatter(B_cyc_norms, B_cut_norms, s=10, alpha=0.5)
    ax2.set_xlabel('|B| from cycle component (T)')
    ax2.set_ylabel('|B| from cut component (T)')
    ax2.set_title('Cycle vs Cut Field Magnitude\n'
                   'Cut is exactly zero at centroid (not just small)')
    ax2.set_ylim(-1e-20, max(B_cyc_norms) * 0.1)
    ax2.axhline(0, color='red', linewidth=1, linestyle='--')
    ax2.text(0.5, 0.85, f'max |B_cut| = {max(B_cut_norms):.1e} T\n'
             f'(machine zero — this is Integer(0))',
             transform=ax2.transAxes, fontsize=9, ha='center',
             bbox=dict(boxstyle='round', facecolor='lightyellow'))
    _stamp(ax2, 'G', 'Biot-Savart, centroid')

    fig.tight_layout()
    return _save(fig, 'fig02_cut_annihilation', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 3: SELECTIVITY TRANSITION (radial profile)
# ═══════════════════════════════════════════════════════════════════

def plot_selectivity_profile(L: float = 0.1, n_points: int = 80,
                              output_dir: str = ".") -> str:
    """
    Show how cut visibility grows as you move away from centroid.
    At centroid: selectivity = ∞ (cut invisible).
    At ~0.36L: crossover (cycle = cut).
    Beyond: cut dominates.

    This is the fundamental spatial structure of K₄ field control.
    """
    V = fe.make_vertices(L)
    M_f = tk.M.astype(float)
    G_f = tk.G.astype(float)

    # Unit excitations
    w_unit = np.array([1.0, 0.0, 0.0])
    u_unit = np.array([1.0, 0.0, 0.0])
    I_cyc = M_f @ w_unit
    I_cut = G_f @ u_unit

    # Radial scan along C₃ axis (toward V0)
    v0_dir = V[0] / np.linalg.norm(V[0])
    r_values = np.linspace(0.001 * L, 0.8 * L, n_points)
    B_cyc_profile = []
    B_cut_profile = []
    selectivity = []

    for r in r_values:
        point = r * v0_dir
        F = fe.field_matrix(point, V)
        b_cyc = np.linalg.norm(F @ I_cyc)
        b_cut = np.linalg.norm(F @ I_cut)
        B_cyc_profile.append(b_cyc)
        B_cut_profile.append(b_cut)
        selectivity.append(b_cyc / b_cut if b_cut > 1e-30 else 1e6)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Top: field magnitudes
    r_norm = r_values / L
    ax1.semilogy(r_norm, B_cyc_profile, 'b-', linewidth=2, label='|B| from cycle (w₁=1)')
    ax1.semilogy(r_norm, B_cut_profile, 'r-', linewidth=2, label='|B| from cut (u₁=1)')
    ax1.set_ylabel('|B| (T)')
    ax1.set_title(f'Radial Field Profiles Along C₃ Axis (toward V₀)\n'
                   f'L = {L} m, unit excitation in first mode')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    _stamp(ax1, 'M', 'Biot-Savart, C₃ axis', 'off-centroid = model-dependent')

    # Bottom: selectivity ratio
    ax2.semilogy(r_norm, selectivity, 'k-', linewidth=2)
    ax2.axhline(1, color='gray', linestyle='--', alpha=0.5, label='Crossover (cycle = cut)')

    # Find crossover
    for i in range(len(selectivity) - 1):
        if selectivity[i] >= 1 and selectivity[i+1] < 1:
            cross_r = r_norm[i]
            ax2.axvline(cross_r, color='orange', linestyle=':', linewidth=1.5,
                       label=f'Crossover at r ≈ {cross_r:.2f}L')
            break

    ax2.set_xlabel('Distance from centroid (r/L)')
    ax2.set_ylabel('Selectivity (|B_cycle| / |B_cut|)')
    ax2.set_title('Selectivity: How "Invisible" is the Cut Channel?')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.01, 1e4)
    _stamp(ax2, 'M', 'Biot-Savart, C₃ axis')

    fig.tight_layout()
    return _save(fig, 'fig03_selectivity_profile', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 4: ANISOTROPY (κ = 2 demonstration)
# ═══════════════════════════════════════════════════════════════════

def plot_anisotropy(L: float = 0.1, output_dir: str = ".") -> str:
    """
    Demonstrate P13: the universal centroid anisotropy κ = 2.
    Shows the B-field response to unit cycle excitation in all directions.
    The response ellipsoid has axis ratio 2:1.
    """
    V = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V)
    FM = F0 @ tk.M.astype(float)

    # Sweep unit sphere in w-space
    n = 200
    phi = np.linspace(0, 2*np.pi, n)
    theta = np.linspace(0, np.pi, n//2)
    B_magnitudes = []
    B_vectors = []

    for t in theta:
        for p in phi:
            w = np.array([np.sin(t)*np.cos(p), np.sin(t)*np.sin(p), np.cos(t)])
            B = FM @ w
            B_magnitudes.append(np.linalg.norm(B))
            B_vectors.append(B)

    B_magnitudes = np.array(B_magnitudes)
    svs = np.linalg.svd(FM, compute_uv=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: histogram of |B| for unit w
    ax1.hist(B_magnitudes, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(svs[0], color='red', linewidth=2, linestyle='--',
                label=f'σ₁ = σ₂ = {svs[0]:.6f} (strong)')
    ax1.axvline(svs[2], color='orange', linewidth=2, linestyle='--',
                label=f'σ₃ = {svs[2]:.6f} (weak)')
    ax1.set_xlabel('|B| at centroid from ‖w‖=1 excitation (T)')
    ax1.set_ylabel('Count')
    ax1.set_title('P13: Response Distribution for Unit Cycle Excitation\n'
                   f'κ = σ₁/σ₃ = {svs[0]/svs[2]:.4f} (theorem: exactly 2)')
    ax1.legend(fontsize=9)
    _stamp(ax1, 'G', 'Biot-Savart, centroid')

    # Right: singular value bar chart across simplex dimensions
    dims = [3, 4, 5, 6]  # K₃, K₄, K₅, K₆
    kappas = [np.sqrt(d) for d in dims]
    colors = ['lightgray', 'steelblue', 'lightgray', 'lightgray']
    ax2.bar([f'K₃\n(triangle)' , f'K₄\n(tetrahedron)', f'K₅\n(5-cell)', f'K₆\n(6-cell)'],
            kappas, color=colors, edgecolor='black')
    ax2.set_ylabel('κ = √n (condition number)')
    ax2.set_title('P13: Universal Centroid Anisotropy\n'
                   'κ = √n for any n-simplex')
    for i, (d, k) in enumerate(zip(dims, kappas)):
        ax2.text(i, k + 0.05, f'√{d} = {k:.3f}', ha='center', fontsize=9)
    ax2.axhline(2.0, color='red', linestyle=':', alpha=0.5)
    ax2.text(1.5, 2.05, 'K₄: κ = 2 exactly', fontsize=8, color='red')
    _stamp(ax2, 'A', 'algebraic — holds for any n-simplex')

    fig.tight_layout()
    return _save(fig, 'fig04_anisotropy', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 5: NULL TETRAHEDRON (face null directions)
# ═══════════════════════════════════════════════════════════════════

def plot_null_tetrahedron(L: float = 0.1, output_dir: str = ".") -> str:
    """
    Show the null tetrahedron: each face center has one invisible cut
    direction. These form a second tetrahedron in cut-coordinate space.
    """
    from .null_tetrahedron import FACE_NULL_DIRECTIONS

    V = fe.make_vertices(L)
    fc = fe.face_centers(V)
    G_f = tk.G.astype(float)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

    # Left: null depth vs distance along each C₃ axis
    for i in range(4):
        v_dir = V[i] / np.linalg.norm(V[i])
        r_values = np.linspace(0.001 * L, 0.4 * L, 60)
        null_depths = []
        for r in r_values:
            point = r * v_dir
            F = fe.field_matrix(point, V)
            FG = F @ G_f
            svs = np.linalg.svd(FG, compute_uv=False)
            null_depths.append(svs[2] / svs[0] if svs[0] > 1e-30 else 0)
        ax1.semilogy(r_values / L, null_depths, linewidth=2,
                    label=f'Toward V{i} (null at F{i})')

    ax1.set_xlabel('Distance from centroid (r/L)')
    ax1.set_ylabel('Null depth (σ₃/σ₁ of F·G)')
    ax1.set_title('Cut-Space Null Depth Along C₃ Symmetry Axes\n'
                   'At centroid: 0 (entire cut space null). Off-centroid: 1D null emerges.')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    _stamp(ax1, 'G/M', 'Biot-Savart, on-axis [G], depth values [M]')

    # Right: table of null directions
    table_data = []
    for i in range(4):
        u = FACE_NULL_DIRECTIONS[f"F{i}"]
        # Verify null at face center
        F_face = fe.field_matrix(fc[i], V)
        FGu = F_face @ G_f @ u
        residual = np.linalg.norm(FGu)
        table_data.append([
            f'F{i}', f'V{i}',
            f'[{int(u[0])},{int(u[1])},{int(u[2])}]',
            f'{residual:.1e}'
        ])

    ax2.axis('off')
    table = ax2.table(
        cellText=table_data,
        colLabels=['Face', 'Opp. Vertex', 'Null u', '|F·G·u|'],
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.0)
    ax2.set_title('Face Null Directions [G]\n'
                   'u₀ = u₁ + u₂ + u₃ (simplex relation [A])\n'
                   'Vertex V_i injection is invisible at opposite face F_i',
                   fontsize=10)

    fig.tight_layout()
    return _save(fig, 'fig05_null_tetrahedron', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 6: FIELD SLICES (B-field in centroid plane)
# ═══════════════════════════════════════════════════════════════════

def plot_field_slice(L: float = 0.1, n_grid: int = 25,
                     z_plane: float = 0.0,
                     w: np.ndarray = None, u_coil: np.ndarray = None,
                     title_extra: str = "",
                     output_dir: str = ".") -> str:
    """
    Plot B-field magnitude and direction on an XY slice.
    Shows how cycle and cut excitations produce different field patterns.
    """
    if w is None:
        w = np.array([0.0, 0.0, 1.0])  # default: w₃ = 1
    if u_coil is None:
        u_coil = np.zeros(3)

    V = fe.make_vertices(L)
    M_f = tk.M.astype(float)
    G_f = tk.G.astype(float)
    I = M_f @ w + G_f @ u_coil

    extent = 0.6 * L
    x = np.linspace(-extent, extent, n_grid)
    y = np.linspace(-extent, extent, n_grid)
    X, Y = np.meshgrid(x, y)
    Bmag = np.zeros_like(X)
    Bx_grid = np.zeros_like(X)
    By_grid = np.zeros_like(X)

    for i in range(n_grid):
        for j in range(n_grid):
            r = np.array([X[i,j], Y[i,j], z_plane])
            F = fe.field_matrix(r, V)
            B = F @ I
            Bmag[i,j] = np.linalg.norm(B)
            Bx_grid[i,j] = B[0]
            By_grid[i,j] = B[1]

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.pcolormesh(X*1e3, Y*1e3, Bmag*1e6, shading='auto', cmap='viridis')
    plt.colorbar(im, ax=ax, label='|B| (µT)')

    # Quiver (subsample for clarity)
    step = max(1, n_grid // 12)
    ax.quiver(X[::step, ::step]*1e3, Y[::step, ::step]*1e3,
              Bx_grid[::step, ::step], By_grid[::step, ::step],
              color='white', alpha=0.7, scale_units='inches', scale=Bmag.max()*8)

    # Mark vertices (projected)
    for i, v in enumerate(V):
        ax.plot(v[0]*1e3, v[1]*1e3, 'r^', markersize=8)
        ax.text(v[0]*1e3 + 1, v[1]*1e3 + 1, f'V{i}', color='red', fontsize=8)

    # Mark centroid
    ax.plot(0, 0, 'y*', markersize=12)

    w_str = f'w=[{w[0]:.1f},{w[1]:.1f},{w[2]:.1f}]'
    u_str = f'u=[{u_coil[0]:.1f},{u_coil[1]:.1f},{u_coil[2]:.1f}]'
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(f'B-Field in z={z_plane*1e3:.1f}mm Plane\n'
                 f'{w_str}, {u_str} {title_extra}')
    _stamp(ax, 'M', f'Biot-Savart, z={z_plane}m slice')

    return _save(fig, f'fig06_field_slice_z{z_plane*1e3:.0f}mm', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 7: CYCLE vs CUT FIELD PATTERNS (side-by-side)
# ═══════════════════════════════════════════════════════════════════

def plot_cycle_vs_cut(L: float = 0.1, n_grid: int = 25,
                      output_dir: str = ".") -> str:
    """
    Side-by-side: pure cycle excitation vs pure cut excitation.
    Shows how different the spatial patterns are, despite both being
    currents in the same 6 edges.
    """
    V = fe.make_vertices(L)
    M_f = tk.M.astype(float)
    G_f = tk.G.astype(float)

    # Cycle: w = [0,0,1] → produces Bz-dominant field at centroid
    I_cyc = M_f @ np.array([0.0, 0.0, 1.0])
    # Cut: u = [1,0,0] → invisible at centroid, shapes far field
    I_cut = G_f @ np.array([1.0, 0.0, 0.0])

    extent = 0.5 * L
    x = np.linspace(-extent, extent, n_grid)
    y = np.linspace(-extent, extent, n_grid)
    X, Y = np.meshgrid(x, y)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for ax, I, label, ctype in [(ax1, I_cyc, 'Cycle (w₃=1)', 'cycle'),
                                 (ax2, I_cut, 'Cut (u₁=1)', 'cut')]:
        Bmag = np.zeros_like(X)
        for i in range(n_grid):
            for j in range(n_grid):
                r = np.array([X[i,j], Y[i,j], 0.0])
                F = fe.field_matrix(r, V)
                B = F @ I
                Bmag[i,j] = np.linalg.norm(B)

        im = ax.pcolormesh(X*1e3, Y*1e3, Bmag*1e6, shading='auto', cmap='viridis')
        plt.colorbar(im, ax=ax, label='|B| (µT)')

        # Mark centroid
        ax.plot(0, 0, 'r*', markersize=15)
        B_cent = fe.field_at_centroid(V) @ I
        ax.text(1, 1, f'B₀ = {np.linalg.norm(B_cent)*1e6:.3f} µT',
                fontsize=9, color='red',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Mark vertices
        for i, v in enumerate(V):
            ax.plot(v[0]*1e3, v[1]*1e3, 'w^', markersize=6)

        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title(f'{label}\nz = 0 plane')
        _stamp(ax, 'M', 'Biot-Savart, z=0 slice')

    fig.suptitle('Cycle vs Cut: Same Wires, Different Physics\n'
                 'Cycle controls centroid B. Cut is invisible there but shapes the surround.',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    return _save(fig, 'fig07_cycle_vs_cut', output_dir)


# ═══════════════════════════════════════════════════════════════════
# FIGURE 8: PHYSICS BOUNDARIES (honest scope declaration)
# ═══════════════════════════════════════════════════════════════════

def plot_physics_boundaries(L: float = 0.1, output_dir: str = ".") -> str:
    """
    Honest visual declaration of where the framework's assumptions hold
    and where they break. This is the antidote to overclaiming.
    """
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.axis('off')

    # Build the boundary table
    boundaries = [
        ["ASSUMPTION", "VALID WHEN", "BREAKS WHEN", "CONSEQUENCE"],
        ["Biot-Savart\n(magnetostatic)", "f << c/L\n(f << 3 GHz for L=0.1m)",
         "f > ~10 MHz\n(λ < 30m, displacement\ncurrent matters)",
         "Need retarded potentials\nor full Maxwell solver"],
        ["1D filament\n(zero-thickness wire)", "wire radius << L\nand r >> wire radius",
         "thick conductors,\nobservation near wire",
         "Null depth has physical floor.\nNeed volumetric current model"],
        ["Independent currents\n(no mutual inductance)", "DC or very low f",
         "AC operation where\nback-EMF couples edges",
         "Need Neumann inductance\ntensor L_ij for control"],
        ["E/B orthogonality\nat centroid", "Perfect T_d symmetry",
         "Manufacturing tolerances,\nirregular geometry",
         "F₀·G ≈ 0 (approximate).\nCalibrate F matrix."],
        ["Quasi-static E-field\n(Laplace model)", "No time-varying B\nin the E domain",
         "AC operation:\nFaraday induces E from dB/dt",
         "E/B coupling at frequency.\nDC corner compensation\ncannot fix AC errors."],
        ["κ = 2 anisotropy", "Regular tetrahedron", "Any edge length variation",
         "κ ≠ 2 but system still\nworks — just not isotropic."],
    ]

    table = ax.table(cellText=boundaries[1:], colLabels=boundaries[0],
                     loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 2.2)

    # Color the header
    for j in range(4):
        table[0, j].set_facecolor('#2c3e50')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # Color rows by severity
    colors = ['#e8f5e9', '#fff3e0', '#fff3e0', '#e8f5e9', '#ffebee', '#e8f5e9']
    for i, color in enumerate(colors):
        for j in range(4):
            table[i+1, j].set_facecolor(color)

    ax.set_title('K₄ Framework: Physics Boundaries\n'
                 'Green = currently handled · Orange = acknowledged gap · Red = critical for AC',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    return _save(fig, 'fig08_physics_boundaries', output_dir)


# ═══════════════════════════════════════════════════════════════════
# MASTER: Generate all diagnostic figures
# ═══════════════════════════════════════════════════════════════════

def generate_all(L: float = 0.1, output_dir: str = ".") -> Dict[str, str]:
    """
    Generate the complete diagnostic figure set.
    Returns dict of {figure_name: file_path}.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    figures = {}
    print("Generating diagnostic figures...")

    print("  Fig 1: Tetrahedron geometry...")
    figures['tetrahedron'] = plot_tetrahedron(L, output_dir)

    print("  Fig 2: Cut annihilation demonstration...")
    figures['cut_annihilation'] = plot_cut_annihilation(L, output_dir)

    print("  Fig 3: Selectivity profile...")
    figures['selectivity'] = plot_selectivity_profile(L, output_dir=output_dir)

    print("  Fig 4: Anisotropy (κ = 2)...")
    figures['anisotropy'] = plot_anisotropy(L, output_dir)

    print("  Fig 5: Null tetrahedron...")
    figures['null_tetrahedron'] = plot_null_tetrahedron(L, output_dir)

    print("  Fig 6: Field slice (centroid plane)...")
    figures['field_slice'] = plot_field_slice(L, output_dir=output_dir)

    print("  Fig 7: Cycle vs Cut patterns...")
    figures['cycle_vs_cut'] = plot_cycle_vs_cut(L, output_dir=output_dir)

    print("  Fig 8: Physics boundaries...")
    figures['physics_boundaries'] = plot_physics_boundaries(L, output_dir)

    print(f"\n  {len(figures)} figures generated in {output_dir}/")
    return figures


if __name__ == "__main__":
    figs = generate_all()
    for name, path in figs.items():
        print(f"  {name}: {path}")
