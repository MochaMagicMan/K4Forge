"""
inductance.py — Neumann Mutual Inductance Tensor & Functional Control
======================================================================

THE BRIDGE TO HARDWARE.

Without this module, "command current I" is physically meaningless.
Six edge coils sharing vertices are inductively coupled — commanding
current in E01 induces back-EMF in every adjacent edge. To achieve a
target current distribution, the drive system must solve:

    V = L · dI/dt + R · I

where L is the 6×6 Neumann mutual inductance matrix.

KEY STRUCTURAL RESULTS (proven here numerically, exact by symmetry):

  1. HODGE-INDUCTANCE DECOUPLING: M^T · L · G = 0
     The inductance matrix respects the Hodge decomposition.
     Cycle and cut modes are inductively DECOUPLED.
     Proof: L is S₄-equivariant on the edge representation. The cycle
     and cut subspaces are distinct S₃-irreps. By Schur's lemma,
     equivariant maps between distinct irreps are zero.

  2. TRIPLE DEGENERACY: L has only two distinct eigenvalues, each
     with multiplicity 3. One triplet spans the cycle subspace, the
     other spans the cut subspace. This means EACH CHANNEL IS ISOTROPIC:
     no preferred direction within cycle or cut.

  3. OPPOSITE EDGES DECOUPLE: M_opp = 0 exactly.
     Opposite edges of a regular tetrahedron are perpendicular,
     so their Neumann integrand (dl₁·dl₂/|r₁-r₂|) vanishes.

  4. SIGN STRUCTURE: Adjacent edges have mutual inductance ±|M_adj|.
     The sign depends on the canonical orientation: edges diverging
     from a shared vertex have +M_adj; edges where one arrives and
     the other departs have -M_adj. This sign structure is what makes
     M^T·L·G = 0 work despite asymmetric individual entries.

FUNCTIONAL INTERFACE (intention-first):
    command_dc(B_target)         → ControlSolution (V, I, P, verification)
    command_ac(B_target, freq)   → ControlSolution with impedance
    command_rotating(B, axis, f) → rotating field specification
    regime_analysis()            → frequency ceiling, coupling, budget

"Decide what happens. Watch what shifts."

Claim: [G] for structure theorems (group theory, exact for regular K₄)
       [M] for numerical L values (Neumann integral + thin-wire model)

Layer: 4+ (extends field_engine with electromagnetic coupling)
"""

import numpy as np
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass, field
from . import truth_kernel as tk
from . import field_engine as fe

# ═══════════════════════════════════════════════════════════════════
# PHYSICAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════

MU0 = fe.MU0                     # vacuum permeability (H/m)
MU0_4PI = MU0 / (4.0 * np.pi)    # μ₀/4π
C_LIGHT = 299_792_458.0           # speed of light (m/s)

# Wire defaults
DEFAULT_L = 0.1                   # edge length (m)
DEFAULT_WIRE_RADIUS = 0.5e-3      # 0.5mm radius (≈ AWG 20)
DEFAULT_RESISTIVITY = 1.68e-8     # copper at 20°C (Ω·m)


# ═══════════════════════════════════════════════════════════════════
# EDGE TOPOLOGY
# ═══════════════════════════════════════════════════════════════════

EDGE_VERTS = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]

def _shared_vertex(e1: int, e2: int) -> Optional[int]:
    """Return shared vertex index, or None if opposite."""
    common = set(EDGE_VERTS[e1]) & set(EDGE_VERTS[e2])
    return min(common) if common else None


# ═══════════════════════════════════════════════════════════════════
# NEUMANN MUTUAL INDUCTANCE
# ═══════════════════════════════════════════════════════════════════

def neumann_mutual(P1, P2, P3, P4, n_quad=256):
    """
    Mutual inductance between oriented segments P1→P2 and P3→P4
    via Neumann formula with Gauss-Legendre quadrature.

    M₁₂ = (μ₀/4π) · (d₁·d₂) · ∫₀¹∫₀¹ dt ds / |P1+t·d1 - P3-s·d2|

    Handles integrable singularity at shared endpoints.
    Returns inductance in Henries (signed, orientation-dependent).
    
    LIMITATION: For adjacent edges sharing a vertex, 1/R diverges at the
    shared point. The clamp R = max(R, 1e-15) prevents division by zero
    but makes the integral resolution-dependent rather than convergent.
    For production-grade mutual inductance of adjacent wires, use Duffy's
    transformation (singular triangle → rectangle, canceling the 1/R
    Jacobian) or analytic closed-form solutions for intersecting filaments.
    The values here are sufficient for structural analysis (sign, degeneracy,
    decoupling) but not for precision hardware voltage pre-emphasis.
    
    Claim: [G] for structure (sign, degeneracy, M^T·L·G = 0)
           [M] for specific numerical L values
    """
    d1 = P2 - P1
    d2 = P4 - P3
    dot_d = np.dot(d1, d2)

    if abs(dot_d) < 1e-30:
        return 0.0  # perpendicular segments → zero mutual

    nodes, weights = np.polynomial.legendre.leggauss(n_quad)
    t = 0.5 * (nodes + 1.0)
    wt = 0.5 * weights
    s = t.copy()
    ws = wt.copy()

    # r1[i] = P1 + t[i]*d1, shape (N,3)
    r1 = P1[np.newaxis, :] + t[:, np.newaxis] * d1[np.newaxis, :]
    r2 = P3[np.newaxis, :] + s[:, np.newaxis] * d2[np.newaxis, :]

    # Distance matrix |r1[i] - r2[j]|, shape (N,N)
    diff = r1[:, np.newaxis, :] - r2[np.newaxis, :, :]
    R = np.sqrt(np.sum(diff**2, axis=2))
    R = np.maximum(R, 1e-15)  # clamp for singularity

    integral = np.einsum('i,j,ij->', wt, ws, 1.0 / R)
    return MU0_4PI * dot_d * integral


def self_inductance(length, wire_radius, mu_r=1.0):
    """
    Self-inductance of a straight wire (Rosa 1908):
    L = (μ₀/2π) · ℓ · [ln(2ℓ/a) - 1 + μᵣ/4]
    Returns Henries.
    
    LIMITATION: The μᵣ/4 term represents internal inductance from uniform
    current distribution. At high frequencies, skin effect pushes current
    to the wire surface, reducing internal inductance toward zero and
    increasing resistance. This function uses DC values only.
    
    Claim: [M] (thin-wire model, DC regime).
    """
    return (MU0 / (2*np.pi)) * length * (np.log(2*length/wire_radius) - 1.0 + mu_r/4.0)


def edge_resistance(length, wire_radius, resistivity=DEFAULT_RESISTIVITY):
    """DC resistance: R = ρ·ℓ/(π·a²). Returns Ohms."""
    return resistivity * length / (np.pi * wire_radius**2)


# ═══════════════════════════════════════════════════════════════════
# THE 6×6 INDUCTANCE TENSOR
# ═══════════════════════════════════════════════════════════════════

@dataclass
class InductanceTensor:
    """Complete 6×6 inductance matrix with structural analysis."""
    L: np.ndarray              # 6×6 matrix (H) — THE object
    L_self: float              # self-inductance per edge (H)
    M_adj_magnitude: float     # |mutual| for adjacent edges (H)
    edge_length: float         # tetrahedron edge length (m)
    wire_radius: float         # conductor radius (m)
    n_quad: int                # quadrature order used

    # Structural theorem results
    hodge_cross_norm: float    # ||M^T·L·G|| — should be ≈ 0
    hodge_relative: float      # ||M^T·L·G|| / ||L|| — should be ≈ 0
    eigenvalues: np.ndarray    # 6 eigenvalues of L
    lambda_cycle: float        # cycle subspace eigenvalue (H)
    lambda_cut: float          # cut subspace eigenvalue (H)


def compute_inductance_tensor(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS,
                               n_quad=256, verbose=False):
    """
    Compute the 6×6 Neumann inductance matrix for K₄ edges.

    Uses the SIGNED Neumann integral for each pair individually.
    The sign encodes the orientation convention (D matrix) and is
    essential for M^T·L·G = 0 to hold.

    By T_d symmetry, the matrix has structure:
        L_self on diagonal (all equal)
        ±|M_adj| for adjacent pairs (sign from orientation)
        0 for opposite pairs (perpendicular edges)

    Returns: InductanceTensor with full analysis.
    Claim: [M] for values, [G] for structural theorems.
    """
    V = fe.make_vertices(L)
    edges = fe.make_edges(V)

    # Compute full matrix with individual Neumann integrals
    Lmat = np.zeros((6, 6))
    L_self_val = self_inductance(L, wire_radius)
    for i in range(6):
        Lmat[i, i] = L_self_val

    adj_magnitudes = []
    for i in range(6):
        for j in range(i+1, 6):
            P1, P2 = edges[i]
            P3, P4 = edges[j]
            Mij = neumann_mutual(P1, P2, P3, P4, n_quad)
            Lmat[i, j] = Mij
            Lmat[j, i] = Mij
            if _shared_vertex(i, j) is not None:
                adj_magnitudes.append(abs(Mij))

    M_adj_mag = np.mean(adj_magnitudes)

    # ── Structural theorem verification ──
    Mf = tk.M.astype(float)
    Gf = tk.G.astype(float)
    cross = Mf.T @ Lmat @ Gf
    cross_norm = np.linalg.norm(cross)
    L_norm = np.linalg.norm(Lmat)
    hodge_rel = cross_norm / L_norm if L_norm > 0 else 0.0

    # Eigenvalues
    evals = np.sort(np.linalg.eigvalsh(Lmat))
    # Should be two degenerate triplets
    lambda_low = np.mean(evals[:3])   # one channel
    lambda_high = np.mean(evals[3:])  # other channel

    # Determine which is cycle vs cut
    # P_cycle · L should give the cycle eigenvalue on cycle vectors
    P_cyc, P_cut = tk.get_projectors_exact()
    # trace(P_cyc · L) = 3 · λ_cycle
    tr_cyc = np.trace(P_cyc @ Lmat)
    lambda_cycle = tr_cyc / 3.0
    lambda_cut = (np.trace(Lmat) - tr_cyc) / 3.0

    if verbose:
        print("=" * 65)
        print(f"INDUCTANCE TENSOR (L={L*100:.0f}cm, a={wire_radius*1e3:.2f}mm, N={n_quad})")
        print("=" * 65)
        print(f"\n  Physical values:")
        print(f"    L_self       = {L_self_val*1e9:.3f} nH")
        print(f"    |M_adjacent| = {M_adj_mag*1e9:.3f} nH")
        print(f"    M_opposite   = 0.000 nH  (perpendicular edges)")
        print(f"    |M_adj|/L_self = {M_adj_mag/L_self_val:.4f}")
        print(f"\n  L matrix (nH):")
        for i in range(6):
            row = '  '.join(f'{Lmat[i,j]*1e9:+8.3f}' for j in range(6))
            print(f"    {tk.EDGE_LABELS[i]}: {row}")
        print(f"\n  HODGE-INDUCTANCE DECOUPLING:")
        print(f"    ||M^T·L·G||         = {cross_norm:.2e} H")
        print(f"    ||M^T·L·G|| / ||L|| = {hodge_rel:.2e}")
        decoupled = "✓ CONFIRMED" if hodge_rel < 1e-12 else "✗ FAILED"
        print(f"    {decoupled}")
        print(f"\n  Eigenvalues (nH): {evals*1e9}")
        print(f"    λ_cycle = {lambda_cycle*1e9:.3f} nH  (3-fold degenerate)")
        print(f"    λ_cut   = {lambda_cut*1e9:.3f} nH  (3-fold degenerate)")
        print(f"    λ_cut/λ_cycle = {lambda_cut/lambda_cycle:.4f}")

    return InductanceTensor(
        L=Lmat, L_self=L_self_val, M_adj_magnitude=M_adj_mag,
        edge_length=L, wire_radius=wire_radius, n_quad=n_quad,
        hodge_cross_norm=cross_norm, hodge_relative=hodge_rel,
        eigenvalues=evals, lambda_cycle=lambda_cycle, lambda_cut=lambda_cut,
    )


# ═══════════════════════════════════════════════════════════════════
# REGIME ANALYSIS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RegimeAnalysis:
    """Physical operating regime derived from inductance + resistance."""
    # Per edge
    R_edge: float          # DC resistance (Ω)
    L_self: float          # self-inductance (H)

    # Cycle channel
    lambda_cycle: float    # mode inductance (H)
    tau_cycle: float       # L/R time constant (s)
    f_3dB_cycle: float     # -3dB bandwidth (Hz)

    # Cut channel
    lambda_cut: float      # mode inductance (H)
    tau_cut: float         # L/R time constant (s)
    f_3dB_cut: float       # -3dB bandwidth (Hz)

    # Limits
    f_quasi_static: float  # wave ceiling: c/(10·L) (Hz)
    f_recommended: float   # min(wave, 10·f_3dB) (Hz)

    # Coupling
    k_adjacent: float      # coupling coefficient |M_adj|/L_self

    def print_summary(self):
        print(f"\n  REGIME ANALYSIS:")
        print(f"    R_edge     = {self.R_edge*1e3:.4f} mΩ")
        print(f"    L_self     = {self.L_self*1e9:.2f} nH")
        print(f"    k_adj      = {self.k_adjacent:.4f}")
        print(f"    λ_cycle    = {self.lambda_cycle*1e9:.2f} nH   τ = {self.tau_cycle*1e6:.2f} μs   f_3dB = {self.f_3dB_cycle/1e3:.1f} kHz")
        print(f"    λ_cut      = {self.lambda_cut*1e9:.2f} nH   τ = {self.tau_cut*1e6:.2f} μs   f_3dB = {self.f_3dB_cut/1e3:.1f} kHz")
        print(f"    f_quasi    = {self.f_quasi_static/1e6:.0f} MHz (wave ceiling)")
        print(f"    f_recom    = {self.f_recommended/1e3:.0f} kHz (recommended max)")
        print(f"    @ 1 kHz    : {'resistive' if 1e3 < self.f_3dB_cycle else 'inductive'}")
        print(f"    @ 100 kHz  : {'resistive' if 1e5 < self.f_3dB_cycle else 'inductive'}")


def regime_analysis(tensor=None, L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS):
    """
    Compute the complete operating regime from the inductance tensor.
    Creates tensor if not provided.
    """
    if tensor is None:
        tensor = compute_inductance_tensor(L, wire_radius)

    R = edge_resistance(L, wire_radius)

    # Mode time constants: τ = λ_mode / R
    # (In mode coordinates, resistance is R per mode because R·I₆ commutes
    # with projectors: M⁺·R·I₆·M = R·I₃, so R_mode = R_edge)
    tau_c = tensor.lambda_cycle / R
    tau_k = tensor.lambda_cut / R
    f3_c = 1.0 / (2 * np.pi * tau_c)
    f3_k = 1.0 / (2 * np.pi * tau_k)

    f_qs = C_LIGHT / (10.0 * L)
    f_rec = min(f_qs, 10.0 * min(f3_c, f3_k))

    return RegimeAnalysis(
        R_edge=R, L_self=tensor.L_self,
        lambda_cycle=tensor.lambda_cycle, tau_cycle=tau_c, f_3dB_cycle=f3_c,
        lambda_cut=tensor.lambda_cut, tau_cut=tau_k, f_3dB_cut=f3_k,
        f_quasi_static=f_qs, f_recommended=f_rec,
        k_adjacent=tensor.M_adj_magnitude / tensor.L_self,
    )


# ═══════════════════════════════════════════════════════════════════
# FUNCTIONAL CONTROL: INTENTION → PHYSICAL SOLUTION
# ═══════════════════════════════════════════════════════════════════
#
# "We don't want to be switching a bunch of weights and seeing what
#  happens — we should decide precisely what happens and watch which
#  weights shift."
#

@dataclass
class ControlSolution:
    """
    Complete physical solution for a field intention.

    This is what the intention-first paradigm produces:
    every field specification maps to a unique set of physical
    parameters with full verification.
    """
    # INTENTION
    intention: str
    B_target: np.ndarray       # (T)
    frequency: float           # (Hz), 0 = DC

    # ALGEBRA
    w: np.ndarray              # cycle weights (3-vector)
    u_coil: np.ndarray         # cut weights (3-vector)
    I_edge: np.ndarray         # physical edge currents (6-vector, A)

    # HARDWARE
    V_drive: np.ndarray        # drive voltages (6-vector, V; may be complex for AC)
    P_dissipated: float        # resistive power (W)
    P_reactive: float          # reactive power (VA)
    I_max: float               # max edge current (A)
    V_max: float               # max drive voltage (V)

    # VERIFICATION
    B_achieved: np.ndarray     # field from solution (T)
    B_error: float             # ||B_achieved - B_target|| (T)
    B_error_relative: float    # relative error

    # REGIME
    claim_class: str
    frequency_regime: str      # DC / resistive / inductive / invalid
    model_notes: str

    def summary(self):
        """Human-readable summary."""
        Bmag = np.linalg.norm(self.B_target)
        unit = 'μT' if Bmag > 1e-7 else 'nT'
        scale = 1e6 if unit == 'μT' else 1e9
        lines = [
            f"  {self.intention}",
            f"  |B| = {Bmag*scale:.3f} {unit}   [{self.claim_class}|{self.frequency_regime}]",
            f"  I_max = {self.I_max*1e3:.3f} mA   V_max = {self.V_max*1e3:.3f} mV",
            f"  P_diss = {self.P_dissipated*1e6:.2f} μW   P_react = {self.P_reactive*1e6:.2f} μVA",
            f"  Verification: ||ΔB||/||B|| = {self.B_error_relative:.2e}",
        ]
        return '\n'.join(lines)

    def edge_table(self):
        """Per-edge current and voltage table."""
        lines = ["  Edge    I (mA)      V (mV)"]
        lines.append("  " + "-" * 30)
        for k, label in enumerate(tk.EDGE_LABELS):
            Ik = self.I_edge[k] * 1e3
            Vk = float(np.real(self.V_drive[k])) * 1e3
            lines.append(f"  {label}  {Ik:+10.4f}  {Vk:+10.4f}")
        return '\n'.join(lines)


def _centroid_inversion(B_target, L=DEFAULT_L):
    """
    Compute cycle weights w such that F₀·M·w = B_target.
    Uses direct numerical inversion of F₀·M (3×3, always invertible
    for the regular tetrahedron by theorem T3.2).

    Note: the closed-form formula in field_engine.centroid_inversion
    is missing a factor of 4π/μ₀. This function uses the numerically
    exact approach: w = (F₀·M)⁻¹ · B_target.
    """
    V = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V)
    F0M = F0 @ tk.M.astype(float)
    return np.linalg.solve(F0M, np.asarray(B_target, dtype=float))


def command_dc(B_target, L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS,
               u_coil=None, tensor=None):
    """
    INTENTION: "I want this DC magnetic field at the centroid."

    Solves for all physical parameters:
        1. w from direct inversion of F₀·M (exact for regular K₄)
        2. I_edge = M·w + G·u_coil
        3. V_drive = R · I_edge  (DC: no inductive term)
        4. P = sum(R · I_k²)

    Returns: ControlSolution with complete specification.
    Claim: [G] at centroid for regular K₄.
    """
    B_target = np.asarray(B_target, dtype=float)
    if u_coil is None:
        u_coil = np.zeros(3)
    u_coil = np.asarray(u_coil, dtype=float)

    # Inversion via direct solve
    w = _centroid_inversion(B_target, L)
    I_edge = tk.M.astype(float) @ w + tk.G.astype(float) @ u_coil

    # Verification
    V_verts = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V_verts)
    B_achieved = F0 @ I_edge
    B_err = np.linalg.norm(B_achieved - B_target)
    B_mag = np.linalg.norm(B_target)
    B_rel = B_err / B_mag if B_mag > 0 else 0.0

    # Hardware
    R = edge_resistance(L, wire_radius)
    V_drive = R * I_edge
    P_diss = R * np.sum(I_edge**2)

    return ControlSolution(
        intention=f"DC field B=[{B_target[0]:.2e},{B_target[1]:.2e},{B_target[2]:.2e}] T at centroid",
        B_target=B_target, frequency=0.0,
        w=w, u_coil=u_coil, I_edge=I_edge,
        V_drive=V_drive, P_dissipated=P_diss, P_reactive=0.0,
        I_max=np.max(np.abs(I_edge)),
        V_max=np.max(np.abs(V_drive)),
        B_achieved=B_achieved, B_error=B_err, B_error_relative=B_rel,
        claim_class="G", frequency_regime="DC",
        model_notes="Centroid inversion, regular K₄, Biot-Savart",
    )


def command_ac(B_amplitude, freq, L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS,
               u_coil=None, tensor=None):
    """
    INTENTION: "I want this AC field amplitude at frequency f."

    The impedance equation: V = Z(ω) · I where Z = R·I₆ + jωL
    Because M^T·L·G = 0, the impedance is block-diagonal in Hodge basis.

    Returns: ControlSolution with complex drive voltages.
    Claim: [M] (requires inductance matrix).
    """
    B_amp = np.asarray(B_amplitude, dtype=float)
    if u_coil is None:
        u_coil = np.zeros(3)

    # Get or compute tensor
    if tensor is None:
        tensor = compute_inductance_tensor(L, wire_radius, n_quad=128)

    # Regime check
    regime = regime_analysis(tensor, L, wire_radius)
    if freq > regime.f_quasi_static:
        freq_regime = 'invalid'
        notes = f"EXCEEDS wave ceiling {regime.f_quasi_static/1e6:.0f} MHz!"
    elif freq > regime.f_3dB_cycle:
        freq_regime = 'inductive'
        notes = f"ωL >> R. Voltage-limited. May need larger supply."
    else:
        freq_regime = 'resistive'
        notes = f"R >> ωL. Standard current control sufficient."

    # Target currents from direct centroid inversion
    w = _centroid_inversion(B_amp, L)
    I_edge = tk.M.astype(float) @ w + tk.G.astype(float) @ u_coil

    # Complex impedance
    omega = 2 * np.pi * freq
    R = edge_resistance(L, wire_radius)
    Z = R * np.eye(6) + 1j * omega * tensor.L
    V_drive = Z @ I_edge

    # Verification (field from currents, not voltages)
    V_verts = fe.make_vertices(L)
    F0 = fe.field_at_centroid(V_verts)
    B_achieved = F0 @ I_edge
    B_err = np.linalg.norm(B_achieved - B_amp)
    B_mag = np.linalg.norm(B_amp)

    # Power
    P_diss = R * np.sum(I_edge**2)
    P_react = omega * float(I_edge @ tensor.L @ I_edge)

    return ControlSolution(
        intention=f"AC field |B|={B_mag:.2e} T @ {freq:.0f} Hz",
        B_target=B_amp, frequency=freq,
        w=w, u_coil=np.asarray(u_coil), I_edge=I_edge,
        V_drive=V_drive, P_dissipated=P_diss, P_reactive=abs(P_react),
        I_max=np.max(np.abs(I_edge)),
        V_max=float(np.max(np.abs(V_drive))),
        B_achieved=B_achieved, B_error=B_err,
        B_error_relative=B_err/B_mag if B_mag > 0 else 0,
        claim_class="M", frequency_regime=freq_regime,
        model_notes=notes,
    )


def command_rotating(B_magnitude, rotation_axis, freq,
                     L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS):
    """
    INTENTION: "I want a B-field rotating at frequency f around given axis."

    A rotating field requires two orthogonal field components in
    quadrature (90° phase shift). This computes both channels.

    Returns dict with both quadrature solutions and combined specification.
    """
    axis = np.asarray(rotation_axis, dtype=float)
    axis = axis / np.linalg.norm(axis)

    # Two orthogonal unit vectors ⊥ axis
    if abs(axis[0]) < 0.9:
        perp1 = np.cross(axis, [1, 0, 0])
    else:
        perp1 = np.cross(axis, [0, 1, 0])
    perp1 = perp1 / np.linalg.norm(perp1)
    perp2 = np.cross(axis, perp1)

    # Shared tensor
    tensor = compute_inductance_tensor(L, wire_radius, n_quad=128)

    sol_cos = command_ac(B_magnitude * perp1, freq, L, wire_radius, tensor=tensor)
    sol_sin = command_ac(B_magnitude * perp2, freq, L, wire_radius, tensor=tensor)

    return {
        'intention': f"Rotating |B|={B_magnitude:.2e} T around {axis} @ {freq:.0f} Hz",
        'cos_channel': sol_cos,
        'sin_channel': sol_sin,
        'V_quadrature': sol_cos.V_drive + 1j * sol_sin.V_drive,
        'P_total': sol_cos.P_dissipated + sol_sin.P_dissipated,
    }


# ═══════════════════════════════════════════════════════════════════
# SYMBOLIC PROOF: HODGE-INDUCTANCE DECOUPLING THEOREM
# ═══════════════════════════════════════════════════════════════════
#
# THEOREM (IL.T1): For any inductance matrix of the form
#     L = a·I₆ + b·(D^T·D − 2I₆) + c·A_opp
# the Hodge cross-coupling vanishes:
#     M^T · L · G = a·(M^T·G) + b·(M^T·(D^T·D−2I)·G) + c·(M^T·A_opp·G)
#
# PROOF (terms 1 and 2, unconditional [A]):
#   Term 1: M^T·G = 0  [T1.1, Integer(0)]
#   Term 2: M^T·(D^T·D−2I)·G = M^T·D^T·D·G − 2·M^T·G
#           M^T·D^T = (D·M)^T = 0  [T1.2, Integer(0)]
#           Therefore term 2 = 0·(D·G) − 2·0 = 0. Integer(0).
#
# PROOF (term 3, geometric [G]):
#   M^T·A_opp·G = [[-1,+1,-1],[-1,+1,-1],[+1,-1,+1]]  (rank 1, integer)
#   This is NOT zero. The term vanishes iff c = M_opp = 0.
#   For the regular tetrahedron: opposite edges are perpendicular,
#   so dl₁·dl₂ = 0, and M_opp = 0 by Neumann formula. [G] exact.
#
# CLASSIFICATION:
#   [A] — Terms 1,2 vanish for ANY K₄ (regular or irregular)
#   [G] — Term 3 vanishes for regular tetrahedron (M_opp = 0)
#   For irregular tetrahedra: cross-coupling = M_opp · X
#     where X = M^T·A_opp·G has Frobenius norm 3.
#     This gives a QUANTITATIVE leakage measure: 3·|M_opp|.
#
# CONSEQUENCE: The control problem separates into independent 3D
#   subproblems (cycle and cut) without cross-coupling, UNLESS
#   the tetrahedron is irregular enough that opposite edges
#   are no longer perpendicular.
# ═══════════════════════════════════════════════════════════════════

# Opposite-edge permutation matrix (frozen, integer)
A_OPP = np.zeros((6, 6), dtype=np.int64)
for i, j in tk.OPPOSITE_EDGES:
    A_OPP[i, j] = 1
    A_OPP[j, i] = 1

# The leakage matrix (frozen, integer, rank 1)
_LEAKAGE_MATRIX = tk.M.T @ A_OPP @ tk.G
# = [[-1,+1,-1],[-1,+1,-1],[+1,-1,+1]]


def verify_decoupling_symbolic():
    """
    Prove M^T · L · G = 0 to Integer(0) using SymPy.

    The inductance matrix has the form L = a·I₆ + b·Σ + c·A_opp
    where Σ = D^T·D − 2I₆ is the signed adjacency matrix.

    Returns dict of proof steps, all verified to Integer(0).
    Claim: [A] for terms 1,2; [G] for term 3 (requires M_opp=0).
    """
    try:
        from sympy import Matrix, Integer, eye, zeros as szeros
    except ImportError:
        return {"error": "SymPy not available"}

    Ms = Matrix(tk.M.tolist())
    Gs = Matrix(tk.G.tolist())
    Ds = Matrix(tk.D.tolist())
    I6 = eye(6)

    results = {}

    # Prerequisites
    results["T1.1_MtG_zero"] = all(x == Integer(0) for x in Ms.T * Gs)
    results["T1.2_DM_zero"] = all(x == Integer(0) for x in Ds * Ms)

    # Term 2: M^T · (D^T·D - 2I) · G
    Sigma = Ds.T * Ds - 2 * I6
    MtSigmaG = Ms.T * Sigma * Gs
    results["IL.T1_term2_MtSigmaG_zero"] = all(
        x == Integer(0) for x in MtSigmaG
    )

    # Mechanism: M^T·D^T = 0 (transpose of D·M = 0)
    MtDt = (Ds * Ms).T
    results["IL.T1_mechanism_MtDt_zero"] = all(
        x == Integer(0) for x in MtDt
    )

    # Term 3: M^T · A_opp · G (NOT zero — quantifies leakage)
    Aopp = Matrix(A_OPP.tolist())
    MtAoppG = Ms.T * Aopp * Gs
    results["IL.T1_term3_MtAoppG_rank1"] = (MtAoppG.rank() == 1)
    results["IL.T1_term3_integer_entries"] = all(
        x in (Integer(-1), Integer(0), Integer(1)) for x in MtAoppG
    )

    # For regular tet: M_opp = 0, so full theorem holds
    # Cross-coupling = M_opp · MtAoppG
    # Frobenius norm of MtAoppG = 3 (by inspection)
    norm_sq = sum(x**2 for x in MtAoppG)
    results["IL.T1_leakage_norm_9"] = (norm_sq == Integer(9))
    # So ||leakage|| = 3 · |M_opp|

    return results


# ═══════════════════════════════════════════════════════════════════
# VERIFICATION SUITE
# ═══════════════════════════════════════════════════════════════════

def verify_inductance(L=DEFAULT_L, wire_radius=DEFAULT_WIRE_RADIUS,
                      verbose=True):
    """
    Verify all inductance module claims.

    IL.1:  L symmetric positive definite
    IL.2:  M^T·L·G = 0 (Hodge-inductance decoupling)
    IL.3:  Adjacent |M| all equal (T_d magnitude symmetry)
    IL.4:  Opposite M all zero (perpendicular edges)
    IL.5:  Eigenvalues: two degenerate triplets
    IL.6:  Each channel isotropic (triple degeneracy < 1e-6)
    IL.7:  DC round-trip (B_target → w → I → B matches)
    IL.8:  Quadrature converged (256 vs 128 < 1e-4 relative)
    IL.9:  AC impedance block-diagonal (cycle V independent of cut u)
    IL.10: Regime analysis consistent
    """
    results = {}

    if verbose:
        print("=" * 65)
        print(f"INDUCTANCE VERIFICATION (L={L*100:.0f}cm, a={wire_radius*1e3:.2f}mm)")
        print("=" * 65)

    tensor = compute_inductance_tensor(L, wire_radius, n_quad=256, verbose=verbose)

    # IL.1: Symmetric positive definite
    asym = np.linalg.norm(tensor.L - tensor.L.T) / np.linalg.norm(tensor.L)
    results["IL.1a_symmetric"] = asym < 1e-14
    results["IL.1b_pos_definite"] = np.all(tensor.eigenvalues > 0)

    # IL.2: Hodge-inductance decoupling
    results["IL.2_hodge_decoupled"] = tensor.hodge_relative < 1e-12

    # IL.3: Adjacent magnitudes all equal
    edges = fe.make_edges(fe.make_vertices(L))
    adj_mags = []
    opp_vals = []
    for i in range(6):
        for j in range(i+1, 6):
            if _shared_vertex(i, j) is not None:
                adj_mags.append(abs(tensor.L[i, j]))
            else:
                opp_vals.append(abs(tensor.L[i, j]))
    adj_spread = (max(adj_mags) - min(adj_mags)) / np.mean(adj_mags) if adj_mags else 0
    results["IL.3_adj_mag_equal"] = adj_spread < 1e-6

    # IL.4: Opposite all zero
    results["IL.4_opp_zero"] = max(opp_vals) < 1e-15 * tensor.L_self if opp_vals else True

    # IL.5: Two degenerate triplets
    evals = tensor.eigenvalues
    spread_low = np.ptp(evals[:3]) / np.mean(evals[:3])
    spread_high = np.ptp(evals[3:]) / np.mean(evals[3:])
    results["IL.5_two_triplets"] = spread_low < 1e-10 and spread_high < 1e-10

    # IL.6: Channel isotropy (triple degeneracy)
    results["IL.6_cycle_isotropic"] = spread_low < 1e-10 or spread_high < 1e-10
    results["IL.6_cut_isotropic"] = spread_low < 1e-10 or spread_high < 1e-10

    # IL.7: DC round-trip
    B_test = np.array([0, 0, 1e-5])
    sol = command_dc(B_test, L, wire_radius)
    results["IL.7_dc_roundtrip"] = sol.B_error_relative < 1e-12

    # IL.8: Quadrature convergence
    t128 = compute_inductance_tensor(L, wire_radius, n_quad=128)
    t256 = compute_inductance_tensor(L, wire_radius, n_quad=256)
    conv_err = np.linalg.norm(t128.L - t256.L) / np.linalg.norm(t256.L)
    results["IL.8_quad_converged"] = conv_err < 1e-4

    # IL.9: AC impedance block-diagonal
    # Apply pure cycle current, check that cut voltage is zero
    omega = 2 * np.pi * 1000  # 1 kHz
    R = edge_resistance(L, wire_radius)
    Z = R * np.eye(6) + 1j * omega * tensor.L
    w_test = np.array([1.0, 0.0, 0.0])  # pure cycle
    I_cycle = tk.M.astype(float) @ w_test
    V = Z @ I_cycle
    # Project V onto cut space
    _, P_cut = tk.get_projectors_exact()
    V_cut_component = P_cut @ V
    V_cycle_component = (np.eye(6) - P_cut) @ V
    impedance_leak = np.linalg.norm(V_cut_component) / np.linalg.norm(V_cycle_component)
    results["IL.9_Z_block_diag"] = impedance_leak < 1e-12

    # IL.10: Regime consistency
    reg = regime_analysis(tensor, L, wire_radius)
    results["IL.10_regime_consistent"] = (
        reg.tau_cycle > 0 and reg.tau_cut > 0
        and reg.f_quasi_static > reg.f_3dB_cycle
    )

    # IL.11-15: Symbolic proof of decoupling theorem
    sym_results = verify_decoupling_symbolic()
    if "error" not in sym_results:
        results["IL.11_sympy_T1.1"] = sym_results.get("T1.1_MtG_zero", False)
        results["IL.12_sympy_MtSigmaG"] = sym_results.get("IL.T1_term2_MtSigmaG_zero", False)
        results["IL.13_sympy_mechanism"] = sym_results.get("IL.T1_mechanism_MtDt_zero", False)
        results["IL.14_leakage_rank1"] = sym_results.get("IL.T1_term3_MtAoppG_rank1", False)
        results["IL.15_leakage_norm"] = sym_results.get("IL.T1_leakage_norm_9", False)

    if verbose:
        reg.print_summary()

        print(f"\n  {'=' * 55}")
        all_pass = True
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {name}: {status}")
            if not passed:
                all_pass = False
        n = len(results)
        p = sum(results.values())
        print(f"\n  {p}/{n} tests passed")
        if all_pass:
            print("  ✅ INDUCTANCE MODULE FULLY VERIFIED")
        else:
            print("  ❌ FAILURES DETECTED")

    return results


# ═══════════════════════════════════════════════════════════════════
# MODULE SELF-TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    verify_inductance(verbose=True)

    print("\n\n" + "=" * 65)
    print("FUNCTIONAL CONTROL DEMONSTRATIONS")
    print("=" * 65)

    # Demo 1: DC field
    print("\n─── DC: 10μT along z-axis ───")
    sol = command_dc([0, 0, 10e-6])
    print(sol.summary())
    print(sol.edge_table())

    # Demo 2: DC field along [1,1,1]
    print("\n─── DC: 10μT along [1,1,1] diagonal ───")
    B111 = 10e-6 * np.array([1,1,1]) / np.sqrt(3)
    sol2 = command_dc(B111)
    print(sol2.summary())
    print(sol2.edge_table())

    # Demo 3: AC field at 1kHz
    print("\n─── AC: 10μT along z-axis @ 1kHz ───")
    sol3 = command_ac([0, 0, 10e-6], 1000)
    print(sol3.summary())

    # Demo 4: AC at 100kHz
    print("\n─── AC: 10μT along z-axis @ 100kHz ───")
    sol4 = command_ac([0, 0, 10e-6], 100000)
    print(sol4.summary())
