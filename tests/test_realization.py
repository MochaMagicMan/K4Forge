"""
tests/test_realization.py — Physical Realization Tests
=======================================================

Verifies that the PhysicalRealization adapter layer produces
correct results and integrates with the existing FieldContext pipeline.

Key tests:
  1. Filament realization matches existing build_context exactly
  2. Bundle at r=0 matches filament
  3. Bundle at r>0 degrades F·G gracefully
  4. Solenoid at N=0 matches filament
  5. Solenoid transition: F·G grows with N_turns
  6. Variable apex at h=L*sqrt(2/3) matches regular
  7. Validation returns correct claim ceilings
  8. Current normalization is consistent
"""

import numpy as np
import pytest

from k4_explorer.contracts import ClaimClass, SymmetryClass
from k4_explorer.context import build_context, build_context_from_realization
from k4_explorer.geometry import (
    adapt_regular,
    build_filament_realization,
    build_bundle_realization,
    build_solenoid_realization,
    make_variable_apex,
    generate_bundle_segments,
    generate_solenoid_segments,
)


# ─── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def regular_vertices():
    from k4_frozen.field_engine import make_vertices
    return make_vertices(0.1)


@pytest.fixture
def reference_ctx(regular_vertices):
    """FieldContext from existing pipeline (the ground truth)."""
    spec = adapt_regular(L=0.1)
    return build_context(spec)


# ─── Test 1: Filament matches existing pipeline ────────────────

class TestFilamentRealization:

    def test_field_matrix_matches(self, regular_vertices, reference_ctx):
        """Filament realization F0 must equal field_engine F0."""
        real = build_filament_realization(regular_vertices)
        ctx = build_context_from_realization(real)

        np.testing.assert_allclose(
            ctx.F0, reference_ctx.F0, atol=1e-15,
            err_msg="Filament realization F0 differs from field_engine"
        )

    def test_F0M_inv_matches(self, regular_vertices, reference_ctx):
        real = build_filament_realization(regular_vertices)
        ctx = build_context_from_realization(real)
        np.testing.assert_allclose(
            ctx.F0M_inv, reference_ctx.F0M_inv, atol=1e-12,
        )

    def test_claim_ceiling_G(self, regular_vertices):
        real = build_filament_realization(regular_vertices)
        ctx = build_context_from_realization(real)
        assert ctx.claim_ceiling == ClaimClass.G

    def test_F0G_residual_zero(self, regular_vertices):
        real = build_filament_realization(regular_vertices)
        ctx = build_context_from_realization(real)
        assert ctx.F0G_residual < 1e-12

    def test_edge_count(self, regular_vertices):
        real = build_filament_realization(regular_vertices)
        assert len(real.edges) == 6

    def test_edge_lengths_uniform(self, regular_vertices):
        real = build_filament_realization(regular_vertices)
        np.testing.assert_allclose(real.edge_lengths, 0.1, atol=1e-12)


# ─── Test 2: Bundle ────────────────────────────────────────────

class TestBundleRealization:

    def test_zero_radius_matches_filament(self, regular_vertices, reference_ctx):
        """Bundle at r=0 with parallel wiring = single wire field."""
        real = build_bundle_realization(regular_vertices, N_wires=10, r_bundle=0.0)
        ctx = build_context_from_realization(real)
        # Parallel wiring: each wire at I/10, 10 wires → same as 1 wire
        np.testing.assert_allclose(
            ctx.F0, reference_ctx.F0, atol=1e-14,
            err_msg="Bundle at r=0 should match filament"
        )

    def test_finite_radius_F0G_degrades(self, regular_vertices):
        """F·G should grow with bundle radius."""
        norms = []
        for r in [0.0, 0.001, 0.005, 0.01]:
            real = build_bundle_realization(regular_vertices, N_wires=6, r_bundle=r)
            ctx = build_context_from_realization(real)
            norms.append(ctx.F0G_residual)
        # Should be monotonically increasing (or flat at zero for r=0)
        assert norms[0] < 1e-12, "Zero-radius should have zero F0G"
        assert norms[-1] > norms[0], "F0G should grow with bundle radius"

    def test_claim_degrades_with_radius(self, regular_vertices):
        """Large bundle radius should downgrade claim from [G] to [M]."""
        real = build_bundle_realization(regular_vertices, N_wires=6, r_bundle=0.03)
        from k4_frozen import truth_kernel as tk, field_engine as fe
        validation = real.validate(
            lambda P1, P2, r, I: fe.biot_savart_segment(P1, P2, r, I),
            tk.M.astype(np.int64), tk.G.astype(np.int64),
        )
        # At r_bundle = 0.03 on L=0.1, this is 30% of edge length — pushes F0G > 1e-6
        assert validation["overall_ceiling"] == ClaimClass.M


# ─── Test 3: Solenoid ─────────────────────────────────────────

class TestSolenoidRealization:

    def test_zero_turns_matches_filament(self, regular_vertices, reference_ctx):
        """Solenoid with N=0 should be a straight wire."""
        real = build_solenoid_realization(
            regular_vertices, N_turns=0, r_coil=0.005,
        )
        ctx = build_context_from_realization(real)
        np.testing.assert_allclose(
            ctx.F0, reference_ctx.F0, atol=1e-14,
            err_msg="Solenoid N=0 should match filament"
        )

    def test_F0G_grows_with_turns(self, regular_vertices):
        """More helical turns → larger F·G departure."""
        norms = []
        for N in [0, 2, 10, 50]:
            real = build_solenoid_realization(
                regular_vertices, N_turns=N, r_coil=0.003,
            )
            ctx = build_context_from_realization(real)
            norms.append(ctx.F0G_residual)
        assert norms[0] < 1e-12
        assert norms[-1] > norms[1] > norms[0], \
            f"F0G should grow with N_turns: {norms}"

    def test_cycle_spanning_survives(self, regular_vertices):
        """rank(F·M) should remain 3 even for tight solenoid."""
        real = build_solenoid_realization(
            regular_vertices, N_turns=50, r_coil=0.003,
        )
        from k4_frozen import truth_kernel as tk, field_engine as fe
        validation = real.validate(
            lambda P1, P2, r, I: fe.biot_savart_segment(P1, P2, r, I),
            tk.M.astype(np.int64), tk.G.astype(np.int64),
        )
        assert validation["rank_FM"] == 3, "Cycle spanning should survive"

    def test_variable_spacing(self, regular_vertices):
        """Nonuniform spacing should produce valid segments."""
        real = build_solenoid_realization(
            regular_vertices, N_turns=10, r_coil=0.003,
            spacing_profile=lambda t: 1.0 + 2.0 * abs(t - 0.5),
        )
        # Should not crash, and should have 6 edges
        assert len(real.edges) == 6
        # Each edge should have 10 * 12 = 120 segments
        assert len(real.edges[0].segments) == 120


# ─── Test 4: Variable apex ─────────────────────────────────────

class TestVariableApex:

    def test_regular_height_matches(self, regular_vertices):
        """At h = L*sqrt(2/3), should be a regular tetrahedron."""
        L = 0.1
        h_regular = L * np.sqrt(2 / 3)
        V = make_variable_apex(L, h_regular)

        # All 6 edges should be length L
        from k4_explorer.contracts import EDGE_PAIRS
        lengths = [np.linalg.norm(V[i] - V[j]) for i, j in EDGE_PAIRS]
        np.testing.assert_allclose(lengths, L, atol=1e-12,
                                   err_msg="Regular-height apex should give uniform edges")

    def test_flat_has_different_edges(self):
        """At h=0, apex-base edges differ from base-base edges."""
        V = make_variable_apex(0.1, h=0.0)
        from k4_explorer.contracts import EDGE_PAIRS
        lengths = [np.linalg.norm(V[i] - V[j]) for i, j in EDGE_PAIRS]
        # Base edges (V1-V2, V1-V3, V2-V3 = indices 3,4,5) should be ~L
        # Apex edges (V0-V1, V0-V2, V0-V3 = indices 0,1,2) differ
        assert not np.allclose(lengths, lengths[0], atol=0.001), \
            "Flat tetrahedron should have non-uniform edge lengths"

    def test_MTG_zero_at_any_height(self, regular_vertices):
        """M^T @ G = 0 is a graph property — holds at any height."""
        from k4_frozen import truth_kernel as tk
        MTG = tk.M.T @ tk.G
        assert np.all(MTG == 0), "M^T @ G must be exactly zero (graph property)"

    def test_F0G_degrades_toward_flat(self):
        """F·G should grow as h decreases from regular toward flat."""
        from k4_frozen import field_engine as fe
        L = 0.1
        h_reg = L * np.sqrt(2 / 3)
        norms = []
        for h in [h_reg, h_reg * 0.5, h_reg * 0.1]:
            V = make_variable_apex(L, h)
            F0 = fe.field_matrix(V.mean(axis=0), V)
            from k4_frozen import truth_kernel as tk
            FG = F0 @ tk.G.astype(float)
            norms.append(np.linalg.norm(FG))
        # Regular should be near zero, flat should be larger
        assert norms[0] < 1e-10
        assert norms[-1] > norms[0]


# ─── Test 5: Normalization consistency ─────────────────────────

class TestNormalization:

    def test_bundle_parallel_normalization(self, regular_vertices):
        """
        Bundle with N parallel wires at r=0 should produce the
        SAME field as a single filament (N wires each at I/N = filament).
        """
        real_1 = build_filament_realization(regular_vertices)
        real_N = build_bundle_realization(regular_vertices, N_wires=20, r_bundle=0.0)

        ctx_1 = build_context_from_realization(real_1)
        ctx_N = build_context_from_realization(real_N)

        np.testing.assert_allclose(
            ctx_1.F0, ctx_N.F0, atol=1e-14,
            err_msg="Parallel bundle at r=0 must give same F as filament"
        )

    def test_digest_deterministic(self, regular_vertices):
        """Same realization should always produce same digest."""
        real_a = build_filament_realization(regular_vertices)
        real_b = build_filament_realization(regular_vertices)
        assert real_a.digest() == real_b.digest()

    def test_digest_changes_with_geometry(self, regular_vertices):
        """Different realizations should produce different digests."""
        real_fil = build_filament_realization(regular_vertices)
        real_bun = build_bundle_realization(regular_vertices, N_wires=5, r_bundle=0.001)
        assert real_fil.digest() != real_bun.digest()
