# ═══════════════════════════════════════════════════════════════════
# PHYSICAL REALIZATION — edge geometry models
# ═══════════════════════════════════════════════════════════════════
#
# These types describe HOW each edge is physically built.
# They sit between GeometrySpec (what shape) and FieldContext (what field).
# The adapter in geometry.py builds these; context.py consumes them.

EDGE_PAIRS = ((0,1), (0,2), (0,3), (1,2), (1,3), (2,3))


class EdgeModel(str, Enum):
    """Physical model for a single edge conductor."""
    FILAMENT  = "filament"    # single wire V_i → V_j (baseline)
    BUNDLE    = "bundle"      # N parallel wires along same path
    SOLENOID  = "solenoid"    # helical winding around edge axis
    MEASURED  = "measured"    # from calibration / FEM data
    # RACETRACK never implemented — geometry never modeled correctly


@dataclass
class EdgeRealization:
    """
    Physical realization of one K4 edge.

    segments: list of (P1, P2) endpoint pairs for Biot-Savart.
        For filament: 1 segment.
        For bundle: N segments (parallel straight wires).
        For solenoid: N_turns × segs_per_turn segments (helix polyline).

    wiring: how current distributes across segments.
        "series"   — 1A edge current flows through ALL segments sequentially.
                     Each segment sees 1A. Total field = sum of all.
                     Physical: one continuous wire wound as helix.
        "parallel" — 1A edge current splits across N conductors.
                     Each segment sees 1A/N. Total field = sum / N.
                     Physical: N wires sharing terminals at both vertices.

    For filament: wiring is irrelevant (1 segment).
    For bundle: default "parallel" (N wires sharing vertex terminals).
    For solenoid: always "series" (one continuous wire).
    """
    edge_index: int                  # 0-5, matches EDGE_LABELS ordering
    vertex_pair: Tuple[int, int]     # (i, j)
    model: EdgeModel
    segments: List[Tuple[np.ndarray, np.ndarray]]
    N_turns: int = 1
    wiring: str = "parallel"         # "series" or "parallel"
    parameters: Dict[str, float] = field(default_factory=dict)

    def effective_current_factor(self) -> float:
        """Multiplier for Biot-Savart sum to get field from 1A edge current."""
        if self.wiring == "parallel" and self.N_turns > 1:
            return 1.0 / self.N_turns
        return 1.0  # series: each segment already at full current


@dataclass
class PhysicalRealization:
    """
    Complete physical realization of a K4 tetrahedron.

    This replaces the ideal Biot-Savart model with actual coil geometry.
    The field_matrix_at() method sums segment contributions with correct
    current normalization.

    Normalization contract: F columns always represent the field from
    1A TOTAL edge current, regardless of internal wiring topology.
    """
    vertices: np.ndarray                # (4, 3)
    edges: List[EdgeRealization]        # exactly 6
    edge_lengths: np.ndarray            # (6,) per-edge lengths
    characteristic_length: float        # nominal L (mean or specified)
    symmetry_class: SymmetryClass
    description: str = ""
    current_normalization: str = "total_edge_current"

    def field_matrix_at(self, r: np.ndarray,
                        biot_savart_fn: Optional[Callable] = None) -> np.ndarray:
        """
        Compute F(r): 3×6 field matrix at point r.

        Each column k = total B at r from 1A on edge k (all other edges off).
        biot_savart_fn: callable(P1, P2, r, I) -> B(3,).
            If None, must be injected by the context builder.
        """
        if biot_savart_fn is None:
            raise ValueError(
                "biot_savart_fn must be provided. "
                "Use build_context_from_realization() which injects it."
            )
        F = np.zeros((3, 6))
        for edge_real in self.edges:
            B_unit = np.zeros(3)
            for P1, P2 in edge_real.segments:
                B_unit += biot_savart_fn(P1, P2, r, 1.0)
            B_unit *= edge_real.effective_current_factor()
            F[:, edge_real.edge_index] = B_unit
        return F

    def validate(self, biot_savart_fn: Callable,
                 M: np.ndarray, G: np.ndarray) -> Dict[str, Any]:
        """
        Run extension checklist. Returns diagnostic dict.
        M, G: frozen integer basis matrices (6,3).
        """
        c = self.vertices.mean(axis=0)
        F0 = self.field_matrix_at(c, biot_savart_fn)
        G_f = G.astype(float)
        M_f = M.astype(float)
        FG = F0 @ G_f
        FM = F0 @ M_f
        svs = np.linalg.svd(FM, compute_uv=False)

        norm_FG = float(np.linalg.norm(FG))
        rank_FM = int(np.linalg.matrix_rank(FM, tol=1e-10))
        kappa = float(svs[0] / svs[-1]) if svs[-1] > 1e-30 else float('inf')

        # Per-metric claims
        fg_claim = ClaimClass.G if norm_FG < 1e-12 else ClaimClass.M
        rank_claim = ClaimClass.G if rank_FM == 3 else ClaimClass.H
        cond_claim = ClaimClass.G if kappa < 10 else ClaimClass.M

        # Overall ceiling
        if norm_FG < 1e-12 and rank_FM == 3 and abs(kappa - 2.0) < 0.01:
            overall = ClaimClass.G
        elif norm_FG < 1e-6 and rank_FM == 3:
            overall = ClaimClass.G
        elif rank_FM == 3:
            overall = ClaimClass.M
        else:
            overall = ClaimClass.H

        return {
            "norm_FG": norm_FG,
            "rank_FM": rank_FM,
            "kappa_FM": kappa,
            "svd_FM": svs.tolist(),
            "F0G_preserved": norm_FG < 1e-6,
            "cycle_spanning": rank_FM == 3,
            "fg_claim": fg_claim,
            "rank_claim": rank_claim,
            "conditioning_claim": cond_claim,
            "overall_ceiling": overall,
        }

    def digest(self) -> str:
        """Deterministic hash for artifact provenance."""
        import hashlib
        data = (
            self.vertices.tobytes()
            + self.edge_lengths.tobytes()
            + str([(e.model.value, e.N_turns, e.wiring, len(e.segments))
                   for e in self.edges]).encode()
            + self.description.encode()
        )
        return hashlib.sha256(data).hexdigest()[:16]
