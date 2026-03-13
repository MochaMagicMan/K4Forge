# ═══════════════════════════════════════════════════════════════════
# PHYSICAL REALIZATION BUILDERS
# ═══════════════════════════════════════════════════════════════════
#
# These build PhysicalRealization objects from vertex arrays.
# They generate Biot-Savart segment lists for each edge model.
#
# IMPORT NOTE: biot_savart_segment is NOT called here — these just
# produce the segment geometry. The actual field computation happens
# in PhysicalRealization.field_matrix_at() which receives the
# Biot-Savart callable from the context builder.

from .contracts import (
    EdgeModel, EdgeRealization, PhysicalRealization, EDGE_PAIRS,
)


# ─────────────────────────────────────────────────────────────────
# Segment generators
# ─────────────────────────────────────────────────────────────────

def _transverse_frame(edge_hat: np.ndarray):
    """Build orthonormal (u, v) perpendicular to edge_hat."""
    up = np.array([0., 0., 1.])
    if abs(np.dot(edge_hat, up)) > 0.9:
        up = np.array([0., 1., 0.])
    u = np.cross(edge_hat, up)
    u = u / np.linalg.norm(u)
    v = np.cross(edge_hat, u)
    return u, v


def generate_bundle_segments(
    V_i: np.ndarray,
    V_j: np.ndarray,
    N_wires: int,
    r_bundle: float = 0.0,
) -> list:
    """
    Segment list for N parallel wires bundled along one edge.

    r_bundle = 0: all wires coincide with edge centerline.
    r_bundle > 0: wires distributed in a circle of radius r_bundle
        around the edge, evenly spaced in angle.

    Returns list of (P1, P2) tuples, one per wire.
    """
    if r_bundle <= 0 or N_wires <= 1:
        return [(np.array(V_i, float), np.array(V_j, float))] * max(N_wires, 1)

    edge = np.asarray(V_j, float) - np.asarray(V_i, float)
    edge_hat = edge / np.linalg.norm(edge)
    u, v = _transverse_frame(edge_hat)

    segments = []
    for k in range(N_wires):
        theta = 2 * np.pi * k / N_wires
        offset = r_bundle * (np.cos(theta) * u + np.sin(theta) * v)
        segments.append((V_i + offset, V_j + offset))

    return segments


def generate_solenoid_segments(
    V_i: np.ndarray,
    V_j: np.ndarray,
    N_turns: int,
    r_coil: float,
    segs_per_turn: int = 12,
    spacing_profile = 'uniform',
) -> list:
    """
    Segment list for helical winding around edge axis.

    Parameters
    ----------
    V_i, V_j : edge endpoints
    N_turns : helical turns (0 = straight wire)
    r_coil : helix radius from edge centerline
    segs_per_turn : polyline resolution per turn (12–20)
    spacing_profile : 'uniform' or callable(t)->float
        Controls local pitch. t in [0,1] = normalized edge position.
        Higher values = more spacing (looser winding) at that position.
        Example: lambda t: 1 + 2*abs(t - 0.5)  → tight center, loose ends

    Returns list of (P1, P2) tuples forming the helix polyline.
    """
    V_i = np.asarray(V_i, float)
    V_j = np.asarray(V_j, float)
    edge = V_j - V_i
    L = np.linalg.norm(edge)
    edge_hat = edge / L
    u, v = _transverse_frame(edge_hat)

    if N_turns == 0:
        return [(V_i.copy(), V_j.copy())]

    total_segs = N_turns * segs_per_turn

    # Precompute axial fractions (uniform or variable spacing)
    t_values = np.linspace(0, 1, total_segs + 1)

    if spacing_profile == 'uniform' or not callable(spacing_profile):
        axial_fracs = t_values
    else:
        # Precompute cumulative spacing on a fine grid, then interpolate
        n_quad = max(200, total_segs * 2)
        t_quad = np.linspace(0, 1, n_quad)
        weights = np.array([spacing_profile(t) for t in t_quad])
        weights = np.maximum(weights, 1e-12)  # avoid zeros
        cumulative = np.cumsum(weights)
        cumulative = cumulative / cumulative[-1]  # normalize to [0, 1]
        axial_fracs = np.interp(t_values, t_quad, cumulative)

    # Build helix points
    points = []
    for k in range(total_segs + 1):
        theta = 2 * np.pi * N_turns * t_values[k]
        center = V_i + axial_fracs[k] * edge
        point = center + r_coil * (np.cos(theta) * u + np.sin(theta) * v)
        points.append(point)

    return [(points[k], points[k + 1]) for k in range(len(points) - 1)]


# ─────────────────────────────────────────────────────────────────
# Variable-apex tetrahedron
# ─────────────────────────────────────────────────────────────────

def make_variable_apex(L: float, h: float) -> np.ndarray:
    """
    Vertices for a tetrahedron with equilateral base (edge L) and
    variable apex height h above the base plane.

    h = L * sqrt(2/3)  →  regular tetrahedron (all edges = L)
    h = 0              →  flat / coplanar (apex in base plane)

    Centroid is shifted so it sits near the origin.
    Base edges are always length L; apex-to-base edges vary with h.

    Returns (4, 3) array: V0 = apex, V1/V2/V3 = base.
    """
    r = L / np.sqrt(3)       # base circumradius
    base_z = -h / 4          # shift centroid toward origin

    return np.array([
        [0.0,           0.0,                      3 * h / 4],    # apex
        [r,             0.0,                      base_z],        # base V1
        [-r / 2,        r * np.sqrt(3) / 2,      base_z],        # base V2
        [-r / 2,       -r * np.sqrt(3) / 2,      base_z],        # base V3
    ])


# ─────────────────────────────────────────────────────────────────
# Realization builders (GeometrySpec + edge model → PhysicalRealization)
# ─────────────────────────────────────────────────────────────────

def _compute_edge_lengths(V: np.ndarray) -> np.ndarray:
    """Compute all 6 edge lengths from vertex array."""
    return np.array([
        np.linalg.norm(V[i] - V[j]) for i, j in EDGE_PAIRS
    ])


def build_filament_realization(
    vertices: np.ndarray,
    description: str = "Single filament per edge",
) -> PhysicalRealization:
    """
    Standard single-wire model. Should produce identical field to
    k4_frozen.field_engine.field_matrix().
    """
    V = np.asarray(vertices, float)
    edge_lens = _compute_edge_lengths(V)
    edges = []
    for idx, (i, j) in enumerate(EDGE_PAIRS):
        edges.append(EdgeRealization(
            edge_index=idx,
            vertex_pair=(i, j),
            model=EdgeModel.FILAMENT,
            segments=[(V[i].copy(), V[j].copy())],
            N_turns=1,
            wiring="series",
        ))
    return PhysicalRealization(
        vertices=V,
        edges=edges,
        edge_lengths=edge_lens,
        characteristic_length=float(np.mean(edge_lens)),
        symmetry_class=_classify_symmetry(edge_lens),
        description=description,
    )


def build_bundle_realization(
    vertices: np.ndarray,
    N_wires: int,
    r_bundle: float = 0.0,
    description: str = "",
) -> PhysicalRealization:
    """
    Bundled parallel wire model.

    N_wires parallel conductors sharing terminals at each vertex.
    Wiring: "parallel" — each wire carries I_edge / N_wires.
    At r_bundle=0, field = single wire field (N wires at I/N each = 1× wire).
    At r_bundle>0, field is slightly different due to spread.
    """
    V = np.asarray(vertices, float)
    edge_lens = _compute_edge_lengths(V)
    edges = []
    for idx, (i, j) in enumerate(EDGE_PAIRS):
        segs = generate_bundle_segments(V[i], V[j], N_wires, r_bundle)
        edges.append(EdgeRealization(
            edge_index=idx,
            vertex_pair=(i, j),
            model=EdgeModel.BUNDLE,
            segments=segs,
            N_turns=N_wires,
            wiring="parallel",
            parameters={"r_bundle": r_bundle},
        ))
    if not description:
        description = f"Bundle {N_wires} wires, r={r_bundle*1e3:.1f}mm"
    return PhysicalRealization(
        vertices=V,
        edges=edges,
        edge_lengths=edge_lens,
        characteristic_length=float(np.mean(edge_lens)),
        symmetry_class=_classify_symmetry(edge_lens) if r_bundle == 0
                       else SymmetryClass.IRREGULAR,
        description=description,
    )


def build_solenoid_realization(
    vertices: np.ndarray,
    N_turns: int,
    r_coil: float,
    segs_per_turn: int = 12,
    spacing_profile = 'uniform',
    description: str = "",
) -> PhysicalRealization:
    """
    Helical solenoid model with adjustable spacing.

    Wiring: "series" — one continuous wire, 1A through entire helix.
    """
    V = np.asarray(vertices, float)
    edge_lens = _compute_edge_lengths(V)
    edges = []
    for idx, (i, j) in enumerate(EDGE_PAIRS):
        segs = generate_solenoid_segments(
            V[i], V[j], N_turns, r_coil,
            segs_per_turn=segs_per_turn,
            spacing_profile=spacing_profile,
        )
        edges.append(EdgeRealization(
            edge_index=idx,
            vertex_pair=(i, j),
            model=EdgeModel.SOLENOID,
            segments=segs,
            N_turns=N_turns,
            wiring="series",
            parameters={
                "r_coil": r_coil,
                "segs_per_turn": float(segs_per_turn),
                "spacing": spacing_profile if isinstance(spacing_profile, str)
                           else "custom",
            },
        ))
    if not description:
        description = f"Solenoid {N_turns}T, r={r_coil*1e3:.1f}mm, {spacing_profile}"
    return PhysicalRealization(
        vertices=V,
        edges=edges,
        edge_lengths=edge_lens,
        characteristic_length=float(np.mean(edge_lens)),
        symmetry_class=SymmetryClass.IRREGULAR,  # helix always breaks T_d
        description=description,
    )


def _classify_symmetry(edge_lengths: np.ndarray) -> SymmetryClass:
    """Classify symmetry from edge length variation."""
    mean_L = np.mean(edge_lengths)
    max_dev = np.max(np.abs(edge_lengths - mean_L)) / mean_L
    if max_dev < 1e-10:
        return SymmetryClass.Td_REGULAR
    elif max_dev < 0.001:
        return SymmetryClass.Td_APPROX
    elif max_dev < 0.5:
        return SymmetryClass.IRREGULAR
    else:
        return SymmetryClass.DEGENERATE
