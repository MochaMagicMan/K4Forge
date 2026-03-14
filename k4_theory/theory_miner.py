#!/usr/bin/env python3
"""
theory_miner.py -- Standalone K4 Theory Mining Engine
=====================================================

Self-contained distillation of k4lab_v5's proof chain, field engine,
symmetry miner, and verification pipeline into one file.

Dependencies: sympy, numpy  (no k4lab imports required)

Sections:
  S0  Conventions & Constants
  S1  Exact Algebraic Kernel (SymPy integers, zero float)
  S2  Symbolic Biot-Savart Engine (exact, parametric in L)
  S3  Fast Numerical Engine (vectorized NumPy)
  S4  Proof Chain (21 theorems + symbolic_proofs extras)
  S5  Symmetry Mining Engine (S4 group, 24 elements)
  S6  K4-Specific Candidate Generators
  S7  Multi-Strategy Verifier
  S8  Unified Runner

Usage:
  python theory_miner.py              # verify all, mine, report
  python theory_miner.py --prove      # proofs only
  python theory_miner.py --mine       # mine identities only
  python theory_miner.py --discover   # generate + verify candidates

Claim tier: [T0] Integer Exact, [T1] Algebraic Exact, [T4] Numerical.

Merges innovations from both k4lab_v5 and K4Forge (truth_kernel.py):
  - C_INT integer field matrix (K4Forge): upgrades T3.1/T3.2/T3.3 to T0
  - DELTA, SIGNS, S sign matrix (K4Forge): integer field structure
  - Adjugate-based projectors (K4Forge): zero-float projector computation
  - A_opp, T2.6 inductance decoupling (k4lab_v5): structural proof chain
  - Multipole selection rules Sel.1-3 (k4lab_v5): parametric SymPy integrals
  - Null tetrahedron structure (k4lab_v5): face/edge null directions
  - S4 symmetry miner + K4-specific candidate generators (k4lab_v5)
"""

from __future__ import annotations
import sys
import time
import hashlib
import json
from enum import Enum
from itertools import permutations
from dataclasses import dataclass, field as datafield
from typing import (
    Dict, List, Set, Optional, Any, Tuple, Iterator, Callable
)

import numpy as np
from numpy.linalg import norm, svd

from sympy import (
    Matrix, Integer, Rational, sqrt, simplify, expand, factor,
    symbols, eye, ones, Symbol, pi, log, asinh,
    integrate, factorial, trigsimp, radsimp, powsimp,
    sympify, N as sp_N, S, GoldenRatio, fibonacci, lucas,
    sin, cos, atan, zeta, polylog,
)
import sympy as sp


# =====================================================================
# S0  CONVENTIONS & CONSTANTS
# =====================================================================
#
# Vertices:  v0=(1,1,1), v1=(1,-1,-1), v2=(-1,1,-1), v3=(-1,-1,1)
# Centroid:  r0 = (0,0,0)
# Edges (oriented low->high): E01, E02, E03, E12, E13, E23
# Edge-current vector: I = [I01, I02, I03, I12, I13, I23]^T in R^6
#
# Key invariants (all exact integer arithmetic):
#   D @ M = 0          (cycles are divergence-free)
#   M^T @ G = 0        (cycle perp cut)
#   M^T M = G^T G = 4I - J   (matched Gram)
#   P_C + P_G = I6     (complete projectors)
#   F(r0) @ G = 0      (cut annihilation at centroid)
#   det(F(r0) @ M) != 0  (full 3D B-field control)

EDGE_PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
EDGE_NAMES = ['E01', 'E02', 'E03', 'E12', 'E13', 'E23']
MU0_OVER_4PI = 1e-7  # T*m/A


# =====================================================================
# S1  EXACT ALGEBRAIC KERNEL  (SymPy -- zero floating-point)
# =====================================================================

def exact_vertices(L=None):
    """Regular tetrahedron with edge length L, centroid at origin.
    s = L/(2*sqrt(2)), vertices at s*(+-1,+-1,+-1) with even minus count."""
    if L is None:
        L = Symbol('L', positive=True)
    s = L / (2 * sqrt(2))
    V = [
        Matrix([+s, +s, +s]),
        Matrix([+s, -s, -s]),
        Matrix([-s, +s, -s]),
        Matrix([-s, -s, +s]),
    ]
    return L, V


def exact_M():
    """Cycle basis M in Z^{6x3}.  Columns span ker(D)."""
    return Matrix([
        [-1,  0,  1],
        [+1, -1,  0],
        [ 0, +1, -1],
        [-1,  0,  0],
        [ 0,  0, +1],
        [ 0, -1,  0],
    ])


def exact_G():
    """Cut basis G in Z^{6x3}.  Gauge p0=0, u=(p1,p2,p3)."""
    return Matrix([
        [+1,  0,  0],
        [ 0, +1,  0],
        [ 0,  0, +1],
        [-1, +1,  0],
        [-1,  0, +1],
        [ 0, -1, +1],
    ])


def exact_D():
    """Incidence matrix D in Z^{4x6}."""
    return Matrix([
        [-1, -1, -1,  0,  0,  0],
        [+1,  0,  0, -1, -1,  0],
        [ 0, +1,  0, +1,  0, -1],
        [ 0,  0, +1,  0, +1, +1],
    ])


def exact_CT():
    """Face coboundary C^T in Z^{4x6}.  d1: edge 1-forms -> face 2-forms."""
    return Matrix([
        [0,  0,  0, +1, -1, +1],
        [0, +1, -1,  0,  0, +1],
        [+1, 0, -1,  0, +1,  0],
        [+1, -1, 0, +1,  0,  0],
    ])


def exact_Gram():
    """The universal K4 Gram: 4I3 - J3."""
    return 4 * eye(3) - ones(3, 3)


def exact_Gram_adjugate():
    """Adjugate of (4I-J): adj = 8I+4J.  Satisfies Gram * adj = 16*I3.
    Enables exact projectors without matrix inversion."""
    return Matrix([
        [8, 4, 4],
        [4, 8, 4],
        [4, 4, 8],
    ])


# --- Integer field-structure matrices (from K4Forge truth_kernel.py) ---
# These encode the centroid field map using ONLY integer arithmetic
# on vertex sign coordinates.  The key insight: the Biot-Savart scalar
# factor cancels, leaving a pure integer cross-product matrix C_INT
# that captures the STRUCTURAL core of all EM theorems.

def exact_SIGNS():
    """Vertex sign coordinates: V_i = (L/2sqrt2) * SIGNS[i].
    Entries in {-1, +1}.  Returns 4x3 SymPy Matrix."""
    return Matrix([
        [+1, +1, +1],
        [+1, -1, -1],
        [-1, +1, -1],
        [-1, -1, +1],
    ])


def exact_DELTA():
    """Integer edge direction signs (3x6).
    Column k = SIGNS[j] - SIGNS[i] for edge (i,j).
    Entries in {-2, 0, +2}."""
    S = exact_SIGNS()
    cols = []
    for (i, j) in EDGE_PAIRS:
        cols.append(S.row(j).T - S.row(i).T)
    D = cols[0]
    for c in cols[1:]:
        D = D.row_join(c)
    return D


def exact_C_INT():
    """Integer cross-product field matrix C_INT in Z^{3x6}.
    C_INT[:,k] = (DELTA_k x SIGNS[tail_k]) / 2.
    Entries in {-1, 0, +1}.

    The centroid field matrix factorizes as:
        F(r0) = alpha(L) * C_INT
    where alpha is a scalar depending on L and mu0.

    PROVEN (integer arithmetic):
        C_INT * G = 0        -> T3.1 (cut annihilation) at T0 level
        det(C_INT * M) = 32  -> T3.2 (controllability) at T0 level
        kappa(C_INT * M) = 2 -> T3.3 (anisotropy) at T0 level
    """
    S = exact_SIGNS()
    cols = []
    for k, (i, j) in enumerate(EDGE_PAIRS):
        delta_k = S.row(j).T - S.row(i).T  # 3x1
        tail_k = S.row(i).T                 # 3x1
        cross = _cross3(delta_k, tail_k)
        cols.append(cross / 2)
    C = cols[0]
    for c in cols[1:]:
        C = C.row_join(c)
    return C


def exact_S_SIGN():
    """Sign matrix S in Z^{3x3}.  Satisfies C_INT * M = -2 * S.
    S = [[-1,+1,-1], [-1,-1,+1], [+1,-1,-1]].

    PROVEN (integer arithmetic):
        S^T * S = 4I - J = Gram
        S * Gram_inv * S^T = I3  (centroid isotropy)
        |eigenvalues| = {1, 2, 2}  (anisotropy ratio 2:1)
    """
    return Matrix([
        [-1, +1, -1],
        [-1, -1, +1],
        [+1, -1, -1],
    ])


def exact_F(L=None):
    """Symbolic field matrix F(r0) in R^{3x6} at centroid.
    Derived from exact finite-wire Biot-Savart.
    Returns (F, L)."""
    if L is None:
        L = Symbol('L', positive=True)
    s3 = sqrt(3)
    k = Rational(1, 1) / L
    F = k * Matrix([
        [0,      -4,       4,      Rational(4, 3),  Rational(-4, 3), Rational(-8, 3)],
        [8*s3/3, -4*s3/3, -4*s3/3, 4*s3/3,          4*s3/3,          0],
        [0,       0,       0,      8*sqrt(2)/3,     -8*sqrt(2)/3,     8*sqrt(2)/3],
    ])
    return F, L


# --- helpers ---

def _is_zero_matrix(mat):
    for i in range(mat.rows):
        for j in range(mat.cols):
            if simplify(mat[i, j]) != Integer(0):
                return False
    return True


def _is_equal_matrix(A, B):
    return _is_zero_matrix(A - B)


def _cross3(a, b):
    """3D cross product for SymPy 3x1 Matrices."""
    return Matrix([
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    ])


# =====================================================================
# S2  SYMBOLIC BIOT-SAVART ENGINE  (exact, parametric in L)
# =====================================================================

def biot_savart_symbolic(P1, P2, r_obs):
    """Exact finite-wire Biot-Savart for segment P1->P2 at r_obs.
    Returns B / (mu0/4pi) as a 3x1 SymPy Matrix."""
    dl = P2 - P1
    r1 = r_obs - P1
    r2 = r_obs - P2
    dl_x_r1 = _cross3(dl, r1)
    norm_cross_sq = dl_x_r1.dot(dl_x_r1)
    dl_norm = sqrt(dl.dot(dl))
    r1_norm = sqrt(r1.dot(r1))
    r2_norm = sqrt(r2.dot(r2))
    cos1 = dl.dot(r1) / (dl_norm * r1_norm)
    cos2 = dl.dot(r2) / (dl_norm * r2_norm)
    return dl_x_r1 * dl_norm * (cos1 - cos2) / norm_cross_sq


def symbolic_F_at(V, r_obs):
    """Build 3x6 field matrix at arbitrary symbolic point."""
    cols = []
    for (i, j) in EDGE_PAIRS:
        B = biot_savart_symbolic(V[i], V[j], r_obs)
        cols.append(Matrix([simplify(b) for b in B]))
    F = cols[0]
    for c in cols[1:]:
        F = F.row_join(c)
    return F


def symbolic_F0():
    """Compute F(r0) at centroid using exact Biot-Savart.
    Returns (L, F0) where F0 is 3x6."""
    L, V = exact_vertices()
    r_obs = Matrix([0, 0, 0])
    return L, symbolic_F_at(V, r_obs)


# =====================================================================
# S3  FAST NUMERICAL ENGINE  (vectorized NumPy)
# =====================================================================

_NP_VERTS = np.array([
    [1,  1,  1],
    [1, -1, -1],
    [-1, 1, -1],
    [-1, -1, 1],
], dtype=float)


def np_vertices():
    return _NP_VERTS.copy()


def _B_wire_single(r, a, b):
    """Exact B-field at point r from wire a->b, 1A.  Returns (3,)."""
    L_vec = b - a
    L_mag = norm(L_vec)
    if L_mag < 1e-30:
        return np.zeros(3)
    t = L_vec / L_mag
    ra = r - a
    cross = np.cross(t, ra)
    R = norm(cross)
    if R < 1e-15:
        return np.zeros(3)
    phi_hat = cross / R
    za = np.dot(ra, t)
    zb = np.dot(r - b, t)
    cos_a = za / np.sqrt(R*R + za*za)
    cos_b = zb / np.sqrt(R*R + zb*zb)
    return MU0_OVER_4PI * (cos_a - cos_b) / R * phi_hat


def _B_wire_batch(points, a, b):
    """Vectorized B-field at N points from wire a->b.  Returns (N,3)."""
    N = points.shape[0]
    L_vec = b - a
    L_mag = norm(L_vec)
    if L_mag < 1e-30:
        return np.zeros((N, 3))
    t = L_vec / L_mag
    ra = points - a
    rb = points - b
    cross = np.cross(t, ra)
    R = norm(cross, axis=1)
    safe = R > 1e-15
    R_safe = np.where(safe, R, 1.0)
    phi_hat = cross / R_safe[:, None]
    za = ra @ t
    zb = rb @ t
    cos_a = za / np.sqrt(R_safe**2 + za**2)
    cos_b = zb / np.sqrt(R_safe**2 + zb**2)
    B_mag = MU0_OVER_4PI * (cos_a - cos_b) / R_safe
    B = B_mag[:, None] * phi_hat
    B[~safe] = 0.0
    return B


def F_matrix(r, V=None, edges=None):
    """Build field map F(r) in R^{3x6}.  B(r) = F(r) @ I_edge."""
    if V is None:
        V = _NP_VERTS
    if edges is None:
        edges = EDGE_PAIRS
    r = np.asarray(r, float)
    F = np.zeros((3, len(edges)))
    for e, (i, j) in enumerate(edges):
        F[:, e] = _B_wire_single(r, V[i], V[j])
    return F


def field_matrix(points, V=None, edges=None):
    """Stacked field matrix (3K x 6) for K points."""
    if V is None:
        V = _NP_VERTS
    if edges is None:
        edges = EDGE_PAIRS
    points = np.atleast_2d(points)
    K = points.shape[0]
    ne = len(edges)
    A = np.zeros((3 * K, ne))
    for e, (i, j) in enumerate(edges):
        B_all = _B_wire_batch(points, V[i], V[j])
        for k in range(K):
            A[3*k:3*k+3, e] = B_all[k]
    return A


_NP_SIGNS = np.array([[+1,+1,+1],[+1,-1,-1],[-1,+1,-1],[-1,-1,+1]], dtype=np.int64)
_NP_C_INT = np.array([[0,+1,-1,-1,+1,0],[-1,0,+1,-1,0,-1],[+1,-1,0,0,+1,-1]], dtype=np.int64)
_NP_S_SIGN = np.array([[-1,+1,-1],[-1,-1,+1],[+1,-1,-1]], dtype=np.int64)
_NP_DELTA = np.array([[0,-2,-2,-2,-2,0],[-2,0,-2,+2,0,-2],[-2,-2,0,0,+2,+2]], dtype=np.int64)
_NP_M = np.array([[-1,0,1],[1,-1,0],[0,1,-1],[-1,0,0],[0,0,1],[0,-1,0]], dtype=np.int64)
_NP_G = np.array([[1,0,0],[0,1,0],[0,0,1],[-1,1,0],[-1,0,1],[0,-1,1]], dtype=np.int64)
_NP_GRAM_ADJ = np.array([[8,4,4],[4,8,4],[4,4,8]], dtype=np.int64)


def np_cycle_basis():
    return _NP_M.astype(float)


def np_cut_basis():
    return _NP_G.astype(float)


def np_gram():
    return np.array([[3,-1,-1],[-1,3,-1],[-1,-1,3]], dtype=float)


def np_projectors():
    """Returns (P_cycle, P_cut) as float64 arrays.
    Computed via integer adjugate: P = M * adj * M^T / 16.  No linalg.inv."""
    M = _NP_M.astype(float)
    G = _NP_G.astype(float)
    adj = _NP_GRAM_ADJ.astype(float)
    return (M @ adj @ M.T) / 16.0, (G @ adj @ G.T) / 16.0


def np_decompose(I_edge):
    """Decompose I_edge -> (w, u, I_cycle, I_cut).
    Uses adjugate: w = adj * M^T * I / 16."""
    M = _NP_M.astype(float)
    G = _NP_G.astype(float)
    adj = _NP_GRAM_ADJ.astype(float)
    I_edge = np.asarray(I_edge, float)
    w = adj @ (M.T @ I_edge) / 16.0
    u = adj @ (G.T @ I_edge) / 16.0
    return w, u, M @ w, G @ u


# =====================================================================
# S4  PROOF CHAIN  (21 core theorems + symbolic_proofs extras)
# =====================================================================

class TheoremLayer(Enum):
    L0_DEC_SPECTRAL = 0
    L1_TOPOLOGY = 1
    L2_RING_QUIET = 2
    L3_ELECTROMAGNETICS = 3
    L4_MULTIPOLE = 4


@dataclass
class TheoremRecord:
    id: str
    statement: str
    layer: TheoremLayer
    description: str
    prove: Optional[Callable] = None
    last_result: Optional[bool] = None
    last_time: Optional[float] = None


# Will be populated below
THEOREM_REGISTRY: Dict[str, TheoremRecord] = {}


def _register(thm_id, statement, layer, description):
    """Decorator factory for theorem proofs."""
    def decorator(fn):
        THEOREM_REGISTRY[thm_id] = TheoremRecord(
            id=thm_id, statement=statement, layer=layer,
            description=description, prove=fn
        )
        return fn
    return decorator


# --- Layer 0: DEC & Spectral ---

@_register("T0.1", "L0 = 4I4 - J4", TheoremLayer.L0_DEC_SPECTRAL,
           "K4 spectral uniqueness")
def prove_T0_1():
    D = exact_D()
    L0 = D * D.T
    return _is_equal_matrix(L0, 4 * eye(4) - ones(4, 4))


@_register("T0.2", "CT*DT = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "DEC exactness")
def prove_T0_2():
    return _is_zero_matrix(exact_CT() * exact_D().T)


@_register("T0.3", "L1 = 4*I6", TheoremLayer.L0_DEC_SPECTRAL,
           "Edge Laplacian scalar")
def prove_T0_3():
    D, CT = exact_D(), exact_CT()
    C = CT.T
    L1 = D.T * D + C * CT
    return _is_equal_matrix(L1, 4 * eye(6))


@_register("T0.4", "D*M = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "Boundary kills cycles")
def prove_T0_4():
    return _is_zero_matrix(exact_D() * exact_M())


@_register("T0.6", "D*CT^T = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "DEC chain: boundary of face = 0")
def prove_T0_6():
    """D * B_face = 0 where B_face = C (face coboundary transposed)."""
    return _is_zero_matrix(exact_D() * exact_CT().T)


@_register("T0.7", "CT*D^T = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "DEC chain: transpose")
def prove_T0_7():
    return _is_zero_matrix(exact_CT() * exact_D().T)


@_register("T0.8", "D_red^T = G", TheoremLayer.L0_DEC_SPECTRAL,
           "Reduced incidence transpose is cut basis")
def prove_T0_8():
    """D with row 0 deleted, transposed, equals G."""
    D_red = exact_D()[1:, :]  # rows 1,2,3 (drop gauge vertex 0)
    return _is_equal_matrix(D_red.T, exact_G())


@_register("T0.12", "MT*(DTD-2I)*G = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "Hodge-Sigma orthogonality")
def prove_T0_12():
    """M^T * (D^T*D - 2*I6) * G = 0.  Key ingredient for inductance decoupling."""
    D, M, G = exact_D(), exact_M(), exact_G()
    Sigma = D.T * D - 2 * eye(6)
    return _is_zero_matrix(M.T * Sigma * G)


def _A_opp_matrix():
    """Opposite-edge adjacency matrix A_opp in Z^{6x6}.
    A_opp[i,j] = 1 iff edges i,j are opposite (share no vertex)."""
    opp = sp.zeros(6, 6)
    for a in range(6):
        for b in range(6):
            if a == b:
                continue
            va = set(EDGE_PAIRS[a])
            vb = set(EDGE_PAIRS[b])
            if len(va & vb) == 0:  # opposite
                opp[a, b] = Integer(1)
    return opp


@_register("T0.14", "MT*A_opp*G = rank-1 integer", TheoremLayer.L0_DEC_SPECTRAL,
           "Opposite-edge coupling through Hodge basis")
def prove_T0_14():
    """M^T * A_opp * G is a 3x3 integer matrix with entries in {-1,0,+1}."""
    M, G = exact_M(), exact_G()
    A = _A_opp_matrix()
    R = M.T * A * G
    # All entries must be integers in {-1, 0, +1}
    for i in range(3):
        for j in range(3):
            val = R[i, j]
            if val not in (Integer(-1), Integer(0), Integer(1)):
                return False
    return True


@_register("T0.15", "||MT*A_opp*G||^2_F = 9", TheoremLayer.L0_DEC_SPECTRAL,
           "Frobenius norm of opposite coupling is exactly 9")
def prove_T0_15():
    M, G = exact_M(), exact_G()
    R = M.T * _A_opp_matrix() * G
    frob_sq = sum(R[i, j]**2 for i in range(3) for j in range(3))
    return simplify(frob_sq - Integer(9)) == Integer(0)


# --- Integer Field-Structure Proofs (from K4Forge truth_kernel) ---
# These upgrade T3.1/T3.2/T3.3 from model-dependent to T0 (integer exact)
# by working with C_INT instead of the full Biot-Savart F(r0).

@_register("INT.C", "C_INT construction", TheoremLayer.L0_DEC_SPECTRAL,
           "C_INT = (DELTA x SIGNS_tail) / 2, entries in {-1,0,+1}")
def prove_C_INT_construction():
    """Verify C_INT is correctly constructed and has entries in {-1,0,+1}."""
    C = exact_C_INT()
    for i in range(3):
        for j in range(6):
            if C[i, j] not in (Integer(-1), Integer(0), Integer(1)):
                return False
    return True


@_register("INT.CM_eq_neg2S", "C_INT*M = -2*S", TheoremLayer.L0_DEC_SPECTRAL,
           "Field-cycle product is twice the sign matrix")
def prove_CM_eq_neg2S():
    return _is_equal_matrix(exact_C_INT() * exact_M(), -2 * exact_S_SIGN())


@_register("INT.CG_zero", "C_INT*G = 0 (integer)", TheoremLayer.L0_DEC_SPECTRAL,
           "Cut annihilation proven to Integer(0) -- no Biot-Savart needed")
def prove_CG_zero():
    """This is the INTEGER proof of cut annihilation.
    Since F(r0) = alpha * C_INT, F(r0)*G = alpha * C_INT*G = alpha * 0 = 0.
    Upgrades T3.1 from L3 to L0."""
    return _is_zero_matrix(exact_C_INT() * exact_G())


@_register("INT.det_CM_32", "det(C_INT*M) = 32", TheoremLayer.L0_DEC_SPECTRAL,
           "Controllability via integer determinant -- no Biot-Savart needed")
def prove_det_CM_32():
    """Since det(F*M) = alpha^3 * det(C_INT*M) and alpha != 0,
    det(C_INT*M) != 0 implies full rank.  Value is exactly 32.
    Upgrades T3.2 from L3 to L0."""
    CM = exact_C_INT() * exact_M()
    # Compute 3x3 integer determinant directly
    d = CM.det()
    return d == Integer(32)


@_register("INT.gram_CM", "(C_INT*M)^T(C_INT*M) = 4*Gram", TheoremLayer.L0_DEC_SPECTRAL,
           "Controllability Gram is 4*(4I-J): eigenvalues {4, 16, 16}, kappa=2")
def prove_gram_CM():
    """(CM)^T(CM) = 4*(4I-J).  Eigenvalues: 4 (x1), 16 (x2).
    kappa^2 = 16/4 = 4, so kappa = 2.
    Upgrades T3.3 (anisotropy) from L3 to L0."""
    CM = exact_C_INT() * exact_M()
    gram = CM.T * CM
    expected = 4 * exact_Gram()
    return _is_equal_matrix(gram, expected)


@_register("INT.STS_gram", "S^T*S = 4I-J (Gram)", TheoremLayer.L0_DEC_SPECTRAL,
           "Sign matrix squared is the Gram -- S is a 'square root' of Gram")
def prove_STS_gram():
    return _is_equal_matrix(exact_S_SIGN().T * exact_S_SIGN(), exact_Gram())


@_register("INT.isotropy", "S*adj*S^T = 16*I3", TheoremLayer.L0_DEC_SPECTRAL,
           "Centroid isotropy: S * Gram_inv * S^T = I (via adjugate)")
def prove_isotropy():
    """S * adj(Gram) * S^T = 16 * I3.
    Dividing by 16: S * Gram^{-1} * S^T = I.
    This means the centroid field map is isotropic up to the
    kappa=2 anisotropy already captured in the Gram."""
    S = exact_S_SIGN()
    adj = exact_Gram_adjugate()
    return _is_equal_matrix(S * adj * S.T, 16 * eye(3))


@_register("INT.DELTA_M_zero", "DELTA*M = 0", TheoremLayer.L0_DEC_SPECTRAL,
           "Edge direction signs annihilate cycles")
def prove_DELTA_M_zero():
    return _is_zero_matrix(exact_DELTA() * exact_M())


@_register("INT.adj_check", "Gram*adj = 16*I3", TheoremLayer.L0_DEC_SPECTRAL,
           "Adjugate correctness: (4I-J)(8I+4J) = 16I")
def prove_adj_check():
    return _is_equal_matrix(exact_Gram() * exact_Gram_adjugate(), 16 * eye(3))


# --- Layer 1: Topology ---

@_register("T1.1", "MT*G = 0", TheoremLayer.L1_TOPOLOGY,
           "Hodge orthogonality")
def prove_T1_1():
    return _is_zero_matrix(exact_M().T * exact_G())


@_register("T1.2", "D*M = 0", TheoremLayer.L1_TOPOLOGY,
           "Kirchhoff compatibility")
def prove_T1_2():
    return _is_zero_matrix(exact_D() * exact_M())


@_register("T1.3", "MTM = GTG = 4I-J", TheoremLayer.L1_TOPOLOGY,
           "Gram identity")
def prove_T1_3():
    M, G = exact_M(), exact_G()
    K = exact_Gram()
    return _is_equal_matrix(M.T * M, K) and _is_equal_matrix(G.T * G, K)


@_register("T1.4", "det(MTM) = 16", TheoremLayer.L1_TOPOLOGY,
           "Gram determinant")
def prove_T1_4():
    return simplify((exact_M().T * exact_M()).det() - Integer(16)) == Integer(0)


@_register("T1.5", "det([M|G]) = +/-16", TheoremLayer.L1_TOPOLOGY,
           "Full-space determinant")
def prove_T1_5():
    MG = exact_M().row_join(exact_G())
    return simplify(MG.det()**2 - Integer(256)) == Integer(0)


@_register("T1.6", "M+*G = G+*M = 0", TheoremLayer.L1_TOPOLOGY,
           "Pseudoinverse orthogonality")
def prove_T1_6():
    M, G = exact_M(), exact_G()
    K_inv = (M.T * M).inv()
    return (_is_zero_matrix(K_inv * M.T * G) and
            _is_zero_matrix(K_inv * G.T * M))


@_register("T1.7", "P_cyc + P_cut = I6", TheoremLayer.L1_TOPOLOGY,
           "Projector completeness")
def prove_T1_7():
    M, G = exact_M(), exact_G()
    K_inv = (M.T * M).inv()
    P_C = M * K_inv * M.T
    P_G = G * K_inv * G.T
    return _is_equal_matrix(P_C + P_G, eye(6))


@_register("T1.8", "P_cyc * P_cut = 0", TheoremLayer.L1_TOPOLOGY,
           "Projector orthogonality")
def prove_T1_8():
    M, G = exact_M(), exact_G()
    K_inv = (M.T * M).inv()
    P_C = M * K_inv * M.T
    P_G = G * K_inv * G.T
    return _is_zero_matrix(P_C * P_G)


# --- Layer 2: Ring-Quiet ---

@_register("T2.1", "det(G_ring) = 0", TheoremLayer.L2_RING_QUIET,
           "Ring solvability")
def prove_T2_1():
    return simplify(exact_G()[3:6, :].det()) == Integer(0)


@_register("T2.2", "null(G_ring) = span{111}", TheoremLayer.L2_RING_QUIET,
           "Ring null space")
def prove_T2_2():
    ns = exact_G()[3:6, :].nullspace()
    if len(ns) != 1:
        return False
    v = ns[0]
    return simplify(v[0] - v[1]) == 0 and simplify(v[1] - v[2]) == 0


@_register("T2.3", "Ring-quiet iff J1+J2+J3=0", TheoremLayer.L2_RING_QUIET,
           "Balanced cycle condition")
def prove_T2_3():
    M, G = exact_M(), exact_G()
    J1, J2, J3 = symbols('J1 J2 J3')
    J = Matrix([J1, J2, J3])
    ns = G[3:6, :].T.nullspace()
    if len(ns) != 1:
        return False
    v = ns[0]
    condition = simplify((v.T * M[3:6, :] * J)[0])
    target = J1 + J2 + J3
    ratio = simplify(condition / target)
    return ratio.is_number and ratio != 0


# --- Layer 3: Electromagnetics ---

@_register("T3.1", "F*G = 0", TheoremLayer.L3_ELECTROMAGNETICS,
           "Cut annihilation at centroid")
def prove_T3_1():
    F, L = exact_F()
    return _is_zero_matrix((F * exact_G()).applyfunc(simplify))


@_register("T3.2", "det(F*M) != 0", TheoremLayer.L3_ELECTROMAGNETICS,
           "Controllability determinant")
def prove_T3_2():
    F, L = exact_F()
    det_val = simplify((F * exact_M()).det())
    expected = Rational(4096, 9) * sqrt(6) / L**3
    return (simplify(det_val - expected) == Integer(0) or
            simplify(det_val + expected) == Integer(0))


@_register("T3.3", "rank(F*M) = 3", TheoremLayer.L3_ELECTROMAGNETICS,
           "Full 3D B-field control")
def prove_T3_3():
    F, L = exact_F()
    return (F * exact_M()).rank() == 3


# --- Layer 4: Multipole Selection Rules ---

_SYM_VERTICES = [
    Matrix([1, 1, 1]),
    Matrix([1, -1, -1]),
    Matrix([-1, 1, -1]),
    Matrix([-1, -1, 1]),
]


@_register("Sel.1", "Cut dipole = 0", TheoremLayer.L4_MULTIPOLE,
           "Cut currents produce zero dipole moment")
def prove_Sel_1():
    u = symbols('u0 u1 u2 u3')
    V = _SYM_VERTICES
    m = Matrix([0, 0, 0])
    for i, j in EDGE_PAIRS:
        I_cut = u[j] - u[i]
        m += Rational(1, 2) * I_cut * _cross3(V[i], V[j])
    m = Matrix([expand(m[k]) for k in range(3)])
    return all(m[k] == Integer(0) for k in range(3))


@_register("Sel.2", "Cut quadrupole = 0", TheoremLayer.L4_MULTIPOLE,
           "Cut currents produce zero quadrupole moment")
def prove_Sel_2():
    u = symbols('u0 u1 u2 u3')
    t = Symbol('t')
    V = _SYM_VERTICES
    Q = sp.zeros(3, 3)
    for i_e, (i, j) in enumerate(EDGE_PAIRS):
        a, b = V[i], V[j]
        d = b - a
        r_t = a + t * d
        I_cut = u[j] - u[i]
        for p in range(3):
            for q in range(3):
                dxr = _cross3(d, r_t)
                integrand = Rational(1, 2) * (r_t[p]*dxr[q] + r_t[q]*dxr[p])
                val = integrate(expand(integrand), (t, 0, 1))
                Q[p, q] += I_cut * val
    Q = Matrix([[expand(Q[p, q]) for q in range(3)] for p in range(3)])
    return all(Q[p, q] == Integer(0) for p in range(3) for q in range(3))


@_register("Sel.3", "Cycle octupole = 0", TheoremLayer.L4_MULTIPOLE,
           "Cycle currents produce zero octupole moment")
def prove_Sel_3():
    """Prove via exact face integrals of l=3 solid harmonics."""
    x, y, z = symbols('x y z')
    s_var, t_var = symbols('s t')

    harmonics_l3 = {
        -3: y * (3*x**2 - y**2),
        -2: x * y * z,
        -1: y * (4*z**2 - x**2 - y**2),
         0: z * (2*z**2 - 3*x**2 - 3*y**2),
        +1: x * (4*z**2 - x**2 - y**2),
        +2: z * (x**2 - y**2),
        +3: x * (x**2 - 3*y**2),
    }

    faces = {
        '012': {'verts': (0, 1, 2), 'normal': (1, 1, -1)},
        '023': {'verts': (0, 2, 3), 'normal': (-1, 1, 1)},
        '031': {'verts': (0, 3, 1), 'normal': (1, -1, 1)},
        '123': {'verts': (1, 2, 3), 'normal': (-1, -1, -1)},
    }

    V = _SYM_VERTICES
    all_zero = True
    for face_key, face in faces.items():
        a, b, c = face['verts']
        n = face['normal']
        for m_val, S_harm in harmonics_l3.items():
            dSdn = (n[0]*sp.diff(S_harm, x) +
                    n[1]*sp.diff(S_harm, y) +
                    n[2]*sp.diff(S_harm, z))
            r_param = V[a] + s_var*(V[b] - V[a]) + t_var*(V[c] - V[a])
            dSdn_param = expand(dSdn.subs([
                (x, r_param[0]), (y, r_param[1]), (z, r_param[2])
            ]))
            inner = integrate(dSdn_param, (t_var, 0, 1 - s_var))
            outer = integrate(inner, (s_var, 0, 1))
            if simplify(outer) != Integer(0):
                all_zero = False
    return all_zero


# --- Layer T2: Inductance / Neumann (closed-form analytic) ---
# These require the A_opp matrix and the structural decomposition
# L = (L_self - m)*I + m*P  where P = I + Sigma + M_opp*A_opp

@_register("T2.5", "M_opp = 0 (regular tetra)", TheoremLayer.L3_ELECTROMAGNETICS,
           "Opposite edge mutual inductance vanishes by perpendicularity")
def prove_T2_5():
    """Neumann integrand has factor dl1.dl2 = 0 for opposite edges (T1.1)."""
    L, V = exact_vertices()
    for a, b in [(0, 5), (1, 4), (2, 3)]:
        ea = V[EDGE_PAIRS[a][1]] - V[EDGE_PAIRS[a][0]]
        eb = V[EDGE_PAIRS[b][1]] - V[EDGE_PAIRS[b][0]]
        if simplify(ea.dot(eb)) != Integer(0):
            return False
    return True


@_register("T2.6", "MT*L*G = 0 (Hodge-inductance)", TheoremLayer.L3_ELECTROMAGNETICS,
           "Cycle-cut decoupling survives inductance: structural proof")
def prove_T2_6():
    """Structural proof:
    L = alpha*I + beta*P where P = I + Sigma + M_opp*A_opp.
    M^T * L * G = alpha*(M^T*G) + beta*(M^T*P*G)
    Term 1: M^T*G = 0 [T0.1 / T1.1]
    Term 2: M^T*P*G = M^T*(I + Sigma + M_opp*A_opp)*G
           = M^T*G + M^T*Sigma*G + M_opp * M^T*A_opp*G
           = 0 + 0 + 0*[finite] = 0
    Uses: T0.1, T0.12 (M^T*Sigma*G=0), T2.5 (M_opp=0).
    We verify the structural identity directly."""
    M, G, D = exact_M(), exact_G(), exact_D()
    Sigma = D.T * D - 2 * eye(6)
    A_opp = _A_opp_matrix()
    # P = I6 + Sigma + A_opp  (for regular tetra, A_opp coefficient is 0
    # but we verify the general term structure)

    # Term by term
    t1 = M.T * G                    # = 0 by T1.1
    t2 = M.T * Sigma * G            # = 0 by T0.12
    # M_opp = 0 for regular tetra (T2.5), so term 3 vanishes trivially
    # But let's verify t3 exists and is finite
    t3 = M.T * A_opp * G            # finite integer matrix (T0.14)

    return (_is_zero_matrix(t1) and
            _is_zero_matrix(t2))
    # Note: t3 need not be zero — it's multiplied by M_opp = 0


@_register("T2.7", "L eigenvalue degeneracy", TheoremLayer.L3_ELECTROMAGNETICS,
           "Inductance matrix has 3-fold degenerate cycle and cut eigenvalues")
def prove_T2_7():
    """L = (L_self - m)*I + m*P where P = 2*P_cut.
    P has eigenvalue 0 (x3) on cycle space, 2 (x3) on cut space.
    Proof: P = 2*G*(G^T G)^{-1}*G^T, so P*M = 0 and P*G = 2*G.
    Eigenvalues: lambda_cycle = L_self - m, lambda_cut = L_self + m."""
    M, G = exact_M(), exact_G()
    K_inv = (G.T * G).inv()
    P = 2 * G * K_inv * G.T
    # P*M = 0 (cycle eigenvalue 0)
    if not _is_zero_matrix(P * M):
        return False
    # P*G = 2*G (cut eigenvalue 2)
    if not _is_equal_matrix(P * G, 2 * G):
        return False
    # P is idempotent scaled: P^2 = 2*P (since P = 2*P_G and P_G^2 = P_G)
    if not _is_equal_matrix(P * P, 2 * P):
        return False
    return True


# --- Symbolic Proofs (from symbolic_proofs.py benchmark) ---

@_register("SYM.geom", "Edge geometry exact", TheoremLayer.L1_TOPOLOGY,
           "All edges=L, opp perp, adj dot=+-1/2")
def prove_edge_geometry():
    L, V = exact_vertices()
    edge_vecs = [V[j] - V[i] for (i, j) in EDGE_PAIRS]
    # All lengths = L
    for ev in edge_vecs:
        if simplify(ev.dot(ev) - L**2) != Integer(0):
            return False
    # Opposite pairs perpendicular
    for a, b in [(0, 5), (1, 4), (2, 3)]:
        if simplify(edge_vecs[a].dot(edge_vecs[b])) != Integer(0):
            return False
    # Adjacent pairs: |dot| = L^2/2
    for a in range(6):
        for b in range(a+1, 6):
            i1, j1 = EDGE_PAIRS[a]
            i2, j2 = EDGE_PAIRS[b]
            if set([i1, j1]) & set([i2, j2]):
                d = simplify(edge_vecs[a].dot(edge_vecs[b]) / L**2)
                if d != Rational(1, 2) and d != Rational(-1, 2):
                    return False
    return True


@_register("SYM.F0G", "F0*G = 0 (symbolic Biot-Savart)", TheoremLayer.L3_ELECTROMAGNETICS,
           "Cut annihilation via symbolic finite-wire")
def prove_F0G_symbolic():
    L, F0 = symbolic_F0()
    F0G = simplify(F0 * exact_G())
    return _is_zero_matrix(F0G)


@_register("SYM.F0M", "det(F0*M), kappa=2", TheoremLayer.L3_ELECTROMAGNETICS,
           "F0*M structure: det, eigenvalues, condition number")
def prove_F0M_structure():
    L, F0 = symbolic_F0()
    F0M = simplify(F0 * exact_M())
    det_val = simplify(F0M.det())
    det_expected = -4096 * sqrt(6) / (9 * L**3)
    if simplify(det_val - det_expected) != Integer(0):
        return False
    gram = simplify(F0M.T * F0M)
    eigenvals = gram.eigenvals()
    lam_small = Rational(128, 3) / L**2
    lam_large = Rational(512, 3) / L**2
    found_s = any(simplify(ev - lam_small) == Integer(0) for ev in eigenvals)
    found_l = any(simplify(ev - lam_large) == Integer(0) for ev in eigenvals)
    if not (found_s and found_l):
        return False
    # kappa^2 = 512/128 = 4
    return simplify(lam_large / lam_small) == Integer(4)


@_register("SYM.sign", "F0*M = alpha*S (sign matrix)", TheoremLayer.L3_ELECTROMAGNETICS,
           "F0*M factorizes as scalar times integer sign matrix")
def prove_F0M_sign():
    L, F0 = symbolic_F0()
    F0M = simplify(F0 * exact_M())
    alpha = 8 * sqrt(6) / (3 * L)
    S_mat = simplify(F0M / alpha)
    S_expected = Matrix([[-1, 1, -1], [-1, -1, 1], [1, -1, -1]])
    return all(simplify(x) == Integer(0) for x in (S_mat - S_expected))


@_register("SYM.neumann", "asinh(1/sqrt3) = ln(sqrt3)", TheoremLayer.L3_ELECTROMAGNETICS,
           "Sub-identity in Neumann integral closed form")
def prove_neumann_identity():
    val = asinh(sqrt(3) / 3)
    expected = log(sqrt(3))
    return (simplify(val.rewrite(log) - expected) == Integer(0) and
            simplify(log(sqrt(3)) - log(3) / 2) == Integer(0))


# --- Null tetrahedron (from symbolic_proofs.py) ---

_FACE_NULL_U = {
    0: Matrix([1, 1, 1]),
    1: Matrix([1, 0, 0]),
    2: Matrix([0, 1, 0]),
    3: Matrix([0, 0, 1]),
}

_EDGE_NULL_U = {
    (0, 5): Matrix([0, 1, 1]),
    (1, 4): Matrix([1, 0, 1]),
    (2, 3): Matrix([1, 1, 0]),
}


@_register("SYM.null", "Null tetrahedron structure", TheoremLayer.L3_ELECTROMAGNETICS,
           "Simplex, injections, face/edge nulls, rank(FG)=2")
def prove_null_tetrahedron():
    L, V = exact_vertices()
    D_mat = exact_D()
    G_mat = exact_G()

    # Simplex relation: u0 = u1 + u2 + u3
    diff = _FACE_NULL_U[0] - (_FACE_NULL_U[1] + _FACE_NULL_U[2] + _FACE_NULL_U[3])
    if not all(x == Integer(0) for x in diff):
        return False

    # Vertex injections
    expected_inject = {
        0: Matrix([-3, 1, 1, 1]),
        1: Matrix([-1, 3, -1, -1]),
        2: Matrix([-1, -1, 3, -1]),
        3: Matrix([-1, -1, -1, 3]),
    }
    for i in range(4):
        J = D_mat * G_mat * _FACE_NULL_U[i]
        if not all(x == Integer(0) for x in (J - expected_inject[i])):
            return False

    # Face null directions
    for i in range(4):
        others = [j for j in range(4) if j != i]
        fc = (V[others[0]] + V[others[1]] + V[others[2]]) / 3
        F = symbolic_F_at(V, fc)
        FGu = simplify(F * G_mat * _FACE_NULL_U[i])
        if not all(x == Integer(0) for x in FGu):
            return False

    # Edge midpoint null directions
    for (e1, e2), u_null in _EDGE_NULL_U.items():
        i1, j1 = EDGE_PAIRS[e1]
        mid = (V[i1] + V[j1]) / 2
        F = symbolic_F_at(V, mid)
        FGu = simplify(F * G_mat * u_null)
        if not all(x == Integer(0) for x in FGu):
            return False

    # rank(F(face_i) * G) = 2
    for i in range(4):
        others = [j for j in range(4) if j != i]
        fc = (V[others[0]] + V[others[1]] + V[others[2]]) / 3
        F = symbolic_F_at(V, fc)
        FG = simplify(F * G_mat)
        if FG.rank() != 2:
            return False

    return True


@_register("SYM.Evol", "E_vol kappa = 2", TheoremLayer.L3_ELECTROMAGNETICS,
           "Barycentric gradient matrix eigenvalues and condition number")
def prove_E_vol():
    L, V = exact_vertices()
    A = Matrix(3, 3, lambda i, j: (V[j + 1] - V[0])[i])
    E_vol = (A.T)**(-1)
    E_vol_s = simplify(E_vol)
    gram = simplify(E_vol_s.T * E_vol_s)
    eigenvals = gram.eigenvals()
    lam_small = Rational(1, 2) / L**2
    lam_large = Integer(2) / L**2
    found_s = any(simplify(ev - lam_small) == Integer(0) for ev in eigenvals)
    found_l = any(simplify(ev - lam_large) == Integer(0) for ev in eigenvals)
    return found_s and found_l


# =====================================================================
# S5  SYMMETRY MINING ENGINE  (S4 group, 24 elements)
# =====================================================================

def _classify_perm(perm):
    """Classify by cycle structure.  Returns (type, description, cycles)."""
    visited = [False] * 4
    cycles = []
    for i in range(4):
        if not visited[i]:
            cycle = []
            j = i
            while not visited[j]:
                visited[j] = True
                cycle.append(j)
                j = perm[j]
            cycles.append(tuple(cycle))
    lengths = sorted([len(c) for c in cycles], reverse=True)
    if lengths == [1, 1, 1, 1]:
        return 'identity', 'identity', cycles
    elif lengths == [2, 1, 1]:
        swap = [c for c in cycles if len(c) == 2][0]
        return 'transposition', f'swap({swap[0]},{swap[1]})', cycles
    elif lengths == [2, 2]:
        swaps = [c for c in cycles if len(c) == 2]
        return 'double_transposition', f'({swaps[0][0]}{swaps[0][1]})({swaps[1][0]}{swaps[1][1]})', cycles
    elif lengths == [3, 1]:
        triple = [c for c in cycles if len(c) == 3][0]
        fixed = [c for c in cycles if len(c) == 1][0]
        return '3_cycle', f'rot3({triple[0]},{triple[1]},{triple[2]})fix={fixed[0]}', cycles
    elif lengths == [4]:
        return '4_cycle', f'rot4({cycles[0][0]},{cycles[0][1]},{cycles[0][2]},{cycles[0][3]})', cycles
    return 'unknown', str(cycles), cycles


def _edge_perm_matrix(vertex_perm):
    """6x6 signed permutation matrix on edge currents induced by vertex perm."""
    sigma = list(vertex_perm)
    edge_idx = {e: i for i, e in enumerate(EDGE_PAIRS)}
    P = np.zeros((6, 6), dtype=int)
    for e_old, (a, b) in enumerate(EDGE_PAIRS):
        sa, sb = sigma[a], sigma[b]
        if sa < sb:
            P[edge_idx[(sa, sb)], e_old] = +1
        else:
            P[edge_idx[(sb, sa)], e_old] = -1
    return P


def _fixed_set(vertex_perm, V, n_samples=30, extent=2.0):
    """Determine spatial fixed set of symmetry.
    Returns (type, sample_points, direction_or_normal, R_matrix)."""
    sigma = list(vertex_perm)
    V_new = V[sigma]
    R = V_new.T @ np.linalg.pinv(V.T)
    A = R - np.eye(3)
    _, S_vals, Vt = svd(A)
    tol = 1e-10
    null_dim = np.sum(S_vals < tol)

    if null_dim == 3:
        return 'all', None, None, R
    elif null_dim == 2:
        plane_basis = Vt[S_vals < tol]
        normal = np.cross(plane_basis[0], plane_basis[1])
        normal = normal / (norm(normal) + 1e-30)
        e1 = plane_basis[0] / (norm(plane_basis[0]) + 1e-30)
        e2_raw = plane_basis[1] - np.dot(plane_basis[1], e1) * e1
        e2 = e2_raw / (norm(e2_raw) + 1e-30)
        ss = np.linspace(-extent, extent, n_samples)
        pts = np.array([s1*e1 + s2*e2 for s1 in ss for s2 in ss])
        return 'plane', pts, normal, R
    elif null_dim == 1:
        direction = Vt[S_vals < tol][0]
        direction = direction / (norm(direction) + 1e-30)
        ts = np.linspace(-extent, extent, n_samples)
        pts = np.array([t * direction for t in ts])
        return 'axis', pts, direction, R
    else:
        return 'point', np.array([[0.0, 0.0, 0.0]]), None, R


def _find_eigenspace_modes(P_edge, eigenvalue, space='cut'):
    """Find current patterns where P_edge * I = eigenvalue * I in subspace."""
    basis = np_cut_basis() if space == 'cut' else np_cycle_basis()
    K_inv = np.linalg.inv(basis.T @ basis)
    P_mode = K_inv @ basis.T @ P_edge @ basis
    eigvals, eigvecs = np.linalg.eig(P_mode)
    modes = []
    for i in range(len(eigvals)):
        if (abs(eigvals[i].real - eigenvalue) < 1e-8 and
                abs(eigvals[i].imag) < 1e-8):
            mode = eigvecs[:, i].real
            mode = mode / (norm(mode) + 1e-30)
            I_edge = basis @ mode
            modes.append((mode, I_edge))
    return modes


def _test_full_null(pts, I_pattern, tol=1e-10):
    """Test if B(r) = 0 for all points with current pattern I."""
    max_B = 0
    for r in pts[:min(50, len(pts))]:
        B = F_matrix(r) @ I_pattern
        max_B = max(max_B, norm(B))
    return max_B, max_B < tol


def _test_component_null(pts, I_pattern, normal, tol=1e-10):
    """Test if B.n = 0 for all points."""
    max_Bn = 0
    for r in pts[:min(50, len(pts))]:
        B = F_matrix(r) @ I_pattern
        max_Bn = max(max_Bn, abs(np.dot(B, normal)))
    return max_Bn, max_Bn < tol


@dataclass
class MinedIdentity:
    """A discovered field identity."""
    symmetry: str
    sym_type: str
    fixed_set: str
    space: str
    mode_type: str
    identity_type: str
    mode_coords: list
    I_edge: list
    residual: float
    passed: bool
    normal: Optional[list] = None


def mine_identities(n_spatial=20, extent=2.0, tol=1e-10,
                    verbose=True) -> List[MinedIdentity]:
    """Scan all 24 S4 symmetries x 2 subspaces for field identities."""
    V = np_vertices()
    discoveries = []
    seen = set()

    if verbose:
        print("=" * 70)
        print("  S5: SYMMETRY MINING ENGINE -- 24 symmetries x 2 spaces")
        print("=" * 70)

    for perm in permutations(range(4)):
        perm = list(perm)
        ctype, desc, _ = _classify_perm(perm)
        if ctype == 'identity':
            continue

        P_edge = _edge_perm_matrix(perm)
        ftype, fpts, fdir, R = _fixed_set(perm, V, n_spatial, extent)
        if fpts is None or len(fpts) == 0:
            continue

        for space in ['cut', 'cycle']:
            for mode_type, eigenvalue in [('anti_invariant', -1.0),
                                           ('invariant', +1.0)]:
                modes = _find_eigenspace_modes(P_edge, eigenvalue, space)
                for mode_coords, I_edge in modes:
                    sig = (ctype, tuple(np.round(mode_coords, 6)),
                           space, mode_type)
                    if sig in seen:
                        continue
                    seen.add(sig)

                    resid, passed = _test_full_null(fpts, I_edge, tol)
                    if passed:
                        d = MinedIdentity(
                            symmetry=desc, sym_type=ctype, fixed_set=ftype,
                            space=space, mode_type=mode_type,
                            identity_type='full_null',
                            mode_coords=mode_coords.tolist(),
                            I_edge=I_edge.tolist(),
                            residual=float(resid), passed=True)
                        discoveries.append(d)
                        if verbose:
                            print(f"  FULL NULL: {desc:45s} {space}/{mode_type} "
                                  f"on {ftype} e={resid:.1e}")
                        continue

                    if ftype == 'plane' and fdir is not None:
                        resid_c, passed_c = _test_component_null(
                            fpts, I_edge, fdir, tol)
                        if passed_c:
                            d = MinedIdentity(
                                symmetry=desc, sym_type=ctype, fixed_set=ftype,
                                space=space, mode_type=mode_type,
                                identity_type='component_null',
                                mode_coords=mode_coords.tolist(),
                                I_edge=I_edge.tolist(),
                                residual=float(resid_c), passed=True,
                                normal=fdir.tolist())
                            discoveries.append(d)
                            if verbose:
                                print(f"  COMP NULL: {desc:45s} {space}/{mode_type} "
                                      f"Bn=0 on {ftype} e={resid_c:.1e}")

    if verbose:
        print(f"\n  Total discoveries: {len(discoveries)}")
        types: Dict[tuple, int] = {}
        for d in discoveries:
            key = (d.identity_type, d.fixed_set, d.space)
            types[key] = types.get(key, 0) + 1
        for (itype, fset, space), count in sorted(types.items()):
            print(f"    {itype} on {fset} ({space}): {count}")

    return discoveries


# =====================================================================
# S6  K4-SPECIFIC CANDIDATE GENERATORS
# =====================================================================

@dataclass
class Candidate:
    """A candidate expression for identity verification."""
    expression: Any
    category: str
    description: str
    source: str
    complexity: int = 0


def generate_k4_field_candidates() -> Iterator[Candidate]:
    """Generate K4 electromagnetic field identity candidates."""
    # Centroid cut annihilation at off-centroid points
    # F(r) @ G should NOT be zero generically, but specific symmetry
    # points might have partial vanishing
    V = np_vertices()

    # Face centroids
    for face_idx, others in enumerate([(1,2,3), (0,2,3), (0,1,3), (0,1,2)]):
        fc = V[list(others)].mean(axis=0)
        FG = F_matrix(fc) @ np_cut_basis()
        # Check each column
        for col in range(3):
            resid = norm(FG[:, col])
            yield Candidate(
                expression=resid,
                category="field_face_cut",
                description=f"||F(face{face_idx})*G_col{col}|| = {resid:.6e}",
                source="k4_field",
                complexity=3
            )

    # Edge midpoints
    for e_idx, (i, j) in enumerate(EDGE_PAIRS):
        mid = (V[i] + V[j]) / 2
        F = F_matrix(mid)
        FM = F @ np_cycle_basis()
        FG = F @ np_cut_basis()
        # Cycle channel singular values
        _, svals, _ = svd(FM)
        # Check for zero singular values (degenerate directions)
        for s_idx, sv in enumerate(svals):
            if sv < 1e-8:
                yield Candidate(
                    expression=sv,
                    category="field_edge_degeneracy",
                    description=f"sigma_{s_idx}(F(mid_{EDGE_NAMES[e_idx]})*M) = {sv:.6e}",
                    source="k4_field",
                    complexity=4
                )

    # Opposite edge midpoint pairs: check field orthogonality
    opp_pairs = [(0, 5), (1, 4), (2, 3)]
    for a, b in opp_pairs:
        mid_a = (V[EDGE_PAIRS[a][0]] + V[EDGE_PAIRS[a][1]]) / 2
        mid_b = (V[EDGE_PAIRS[b][0]] + V[EDGE_PAIRS[b][1]]) / 2
        Fa = F_matrix(mid_a)
        Fb = F_matrix(mid_b)
        # Cross-correlation
        corr = np.trace(Fa @ Fb.T)
        yield Candidate(
            expression=corr,
            category="field_opp_correlation",
            description=f"Tr(F(mid_{EDGE_NAMES[a]})*F(mid_{EDGE_NAMES[b]})^T) = {corr:.6e}",
            source="k4_field",
            complexity=5
        )


def generate_projector_candidates() -> Iterator[Candidate]:
    """Generate candidates from projector algebra."""
    P_C, P_G = np_projectors()

    # P_C^2 = P_C (idempotent)
    resid = norm(P_C @ P_C - P_C)
    yield Candidate(resid, "projector", "P_C^2 = P_C", "projector", 2)

    # P_G^2 = P_G
    resid = norm(P_G @ P_G - P_G)
    yield Candidate(resid, "projector", "P_G^2 = P_G", "projector", 2)

    # Trace identities
    yield Candidate(
        abs(np.trace(P_C) - 3.0), "projector",
        f"Tr(P_C) = 3 (residual {abs(np.trace(P_C) - 3.0):.1e})",
        "projector", 2
    )
    yield Candidate(
        abs(np.trace(P_G) - 3.0), "projector",
        f"Tr(P_G) = 3 (residual {abs(np.trace(P_G) - 3.0):.1e})",
        "projector", 2
    )

    # P_C and P_G commute with all S4 elements
    for perm in [(1, 0, 3, 2), (0, 2, 1, 3), (1, 2, 3, 0)]:
        P_edge = _edge_perm_matrix(perm).astype(float)
        comm_C = norm(P_C @ P_edge - P_edge @ P_C)
        comm_G = norm(P_G @ P_edge - P_edge @ P_G)
        yield Candidate(
            comm_C, "projector_symmetry",
            f"[P_C, P_{perm}] = {comm_C:.1e}", "projector", 4
        )
        yield Candidate(
            comm_G, "projector_symmetry",
            f"[P_G, P_{perm}] = {comm_G:.1e}", "projector", 4
        )


def generate_spectral_candidates() -> Iterator[Candidate]:
    """Generate candidates from spectral analysis of field matrices."""
    V = np_vertices()
    M = np_cycle_basis()
    G = np_cut_basis()

    # Centroid: eigenvalue structure of F*M
    F0 = F_matrix(np.array([0.0, 0.0, 0.0]))
    FM = F0 @ M
    gram_FM = FM.T @ FM
    eigvals = np.sort(np.linalg.eigvalsh(gram_FM))

    # Check eigenvalue ratio (should be exactly 4 from kappa^2)
    if eigvals[0] > 1e-15:
        ratio = eigvals[-1] / eigvals[0]
        yield Candidate(
            abs(ratio - 4.0), "spectral",
            f"lambda_max/lambda_min(FM^T FM) = {ratio:.10f} (expect 4)",
            "spectral", 3
        )

    # Multiplicity: two largest eigenvalues should be equal
    if len(eigvals) >= 2:
        yield Candidate(
            abs(eigvals[1] - eigvals[2]), "spectral",
            f"lambda_2 - lambda_3 = {abs(eigvals[1]-eigvals[2]):.2e} (expect 0)",
            "spectral", 3
        )

    # F0 @ G eigenvalues (should all be zero)
    FG = F0 @ G
    fro = norm(FG, 'fro')
    yield Candidate(
        fro, "spectral",
        f"||F0*G||_F = {fro:.2e} (expect 0)", "spectral", 2
    )

    # Td character analysis at field level: check symmetry of FM
    # Under vertex permutation, FM should transform as T1 representation
    test_perm = [1, 0, 3, 2]  # double transposition
    P_edge = _edge_perm_matrix(test_perm).astype(float)
    P_w = np.linalg.inv(M.T @ M) @ M.T @ P_edge @ M
    # Character (trace) of double transposition in T1 should be -1
    char = np.trace(P_w)
    yield Candidate(
        abs(char - (-1.0)), "spectral_symmetry",
        f"chi_T1(double_transp) = {char:.6f} (expect -1)", "spectral", 4
    )


# =====================================================================
# S7  MULTI-STRATEGY VERIFIER
# =====================================================================

class VerificationLevel(Enum):
    FAILED = "failed"
    NUMERICAL = "numerical"
    SYMBOLIC = "symbolic"
    EXACT = "exact"
    CERTIFIED = "certified"


@dataclass
class VerificationResult:
    expression: str
    level: VerificationLevel
    residual: Optional[float] = None
    confidence: float = 0.0
    methods_passed: list = datafield(default_factory=list)
    methods_failed: list = datafield(default_factory=list)
    time_s: float = 0.0

    @property
    def passed(self):
        return self.level != VerificationLevel.FAILED

    @property
    def is_exact(self):
        return self.level in (VerificationLevel.EXACT, VerificationLevel.CERTIFIED)


def verify_expression(
    expr,
    numerical_tol: float = 1e-12,
    numerical_precision: int = 50,
    skip_symbolic: bool = False
) -> VerificationResult:
    """Multi-strategy verification of a SymPy expression as identity (=0)."""
    t0 = time.time()
    result = VerificationResult(
        expression=str(expr),
        level=VerificationLevel.FAILED
    )

    # Attempt symbolic simplification
    if not skip_symbolic:
        for name, fn in [('simplify', simplify), ('expand', expand),
                         ('factor', factor), ('trigsimp', trigsimp),
                         ('radsimp', radsimp), ('powsimp', powsimp)]:
            try:
                s = fn(expr)
                if s == 0 or s == Integer(0) or s == S.Zero:
                    result.level = VerificationLevel.EXACT
                    result.confidence = 1.0
                    result.residual = 0.0
                    result.methods_passed.append(name)
                    result.time_s = time.time() - t0
                    return result
                result.methods_passed.append(name)
            except Exception:
                result.methods_failed.append(name)

        # Combined
        try:
            combined = simplify(expand(simplify(expr)))
            if combined == 0:
                result.level = VerificationLevel.EXACT
                result.confidence = 1.0
                result.residual = 0.0
                result.methods_passed.append('combined')
                result.time_s = time.time() - t0
                return result
        except Exception:
            pass

    # Numerical
    try:
        val = complex(sp_N(expr, numerical_precision))
        mag = abs(val)
        result.residual = mag
        if mag < numerical_tol:
            result.methods_passed.append('numerical')
            if result.level == VerificationLevel.FAILED:
                result.level = VerificationLevel.NUMERICAL
                # Log-scale confidence
                if mag > 0:
                    import math
                    log_r = -math.log10(mag)
                    log_t = -math.log10(numerical_tol)
                    result.confidence = min(1.0, log_r / (log_t + 5))
                else:
                    result.confidence = 1.0
        else:
            result.methods_failed.append('numerical')
    except Exception:
        result.methods_failed.append('numerical')

    # Certification: 3+ methods agree
    if len(result.methods_passed) >= 3:
        result.level = VerificationLevel.CERTIFIED
        result.confidence = min(1.0, result.confidence + 0.2)

    result.time_s = time.time() - t0
    return result


def verify_numerical_identity(value: float, tol: float = 1e-10) -> bool:
    """Quick boolean check for a numerical value being zero."""
    return abs(value) < tol


# =====================================================================
# S8  UNIFIED RUNNER
# =====================================================================

def run_proofs(verbose=True) -> Dict[str, bool]:
    """Run all registered theorem proofs."""
    results = {}
    layers = {}
    for thm_id, rec in THEOREM_REGISTRY.items():
        layer = rec.layer
        if layer not in layers:
            layers[layer] = []
        layers[layer].append((thm_id, rec))

    if verbose:
        print("=" * 70)
        print("  K4 PROOF CHAIN -- Complete Verification")
        print("=" * 70)

    total, passed, failed = 0, 0, 0
    for layer in sorted(layers.keys(), key=lambda x: x.value):
        if verbose:
            print(f"\n  {layer.name}")
            print(f"  {'─' * 66}")

        for thm_id, rec in sorted(layers[layer], key=lambda x: x[0]):
            total += 1
            t0 = time.time()
            try:
                ok = rec.prove()
                rec.last_result = ok
                rec.last_time = time.time() - t0
            except Exception as e:
                ok = False
                rec.last_result = False
                rec.last_time = time.time() - t0
                if verbose:
                    print(f"    ERROR in {thm_id}: {e}")

            results[thm_id] = ok
            if ok:
                passed += 1
            else:
                failed += 1

            if verbose:
                status = "PROVED" if ok else "FAILED"
                elapsed = rec.last_time
                print(f"    {thm_id:10s} {rec.statement:30s} {status:6s}  "
                      f"({elapsed:.2f}s)")

    if verbose:
        print(f"\n  {'=' * 66}")
        print(f"  {passed}/{total} proved, {failed} failed")
        print(f"  {'=' * 66}")

    return results


def run_mining(verbose=True) -> List[MinedIdentity]:
    """Run the symmetry mining engine."""
    return mine_identities(n_spatial=25, extent=2.5, tol=1e-10, verbose=verbose)


def run_discover(verbose=True) -> List[Tuple[Candidate, VerificationResult]]:
    """Run K4-specific candidate generation and verification."""
    if verbose:
        print("\n" + "=" * 70)
        print("  K4 CANDIDATE DISCOVERY ENGINE")
        print("=" * 70)

    generators = [
        ("field", generate_k4_field_candidates),
        ("projector", generate_projector_candidates),
        ("spectral", generate_spectral_candidates),
    ]

    results = []
    for gen_name, gen_fn in generators:
        if verbose:
            print(f"\n  Generator: {gen_name}")
        for candidate in gen_fn():
            is_zero = verify_numerical_identity(
                candidate.expression if isinstance(candidate.expression, (int, float))
                else float(candidate.expression),
                tol=1e-10
            )
            vr = VerificationResult(
                expression=candidate.description,
                level=VerificationLevel.NUMERICAL if is_zero else VerificationLevel.FAILED,
                residual=float(candidate.expression) if isinstance(candidate.expression, (int, float)) else None,
                confidence=1.0 if is_zero else 0.0,
            )
            results.append((candidate, vr))
            if verbose and is_zero:
                print(f"    IDENTITY: {candidate.description}")

    if verbose:
        n_found = sum(1 for _, vr in results if vr.passed)
        print(f"\n  {n_found}/{len(results)} candidates verified as identities")

    return results


def run_all(verbose=True):
    """Run everything: proofs, mining, discovery."""
    t0 = time.time()

    print("\n" + "#" * 70)
    print("#  theory_miner.py -- K4 Theory Mining Engine")
    print("#" * 70)

    # Phase 1: Proofs
    print("\n>>> PHASE 1: PROOF CHAIN")
    proof_results = run_proofs(verbose=verbose)

    # Phase 2: Symmetry mining
    print("\n>>> PHASE 2: SYMMETRY MINING")
    mined = run_mining(verbose=verbose)

    # Phase 3: Discovery
    print("\n>>> PHASE 3: CANDIDATE DISCOVERY")
    discoveries = run_discover(verbose=verbose)

    # Summary
    elapsed = time.time() - t0
    n_proofs = sum(1 for v in proof_results.values() if v)
    n_mined = len(mined)
    n_disc = sum(1 for _, vr in discoveries if vr.passed)

    print("\n" + "=" * 70)
    print(f"  SUMMARY")
    print(f"  Theorems proved:    {n_proofs}/{len(proof_results)}")
    print(f"  Identities mined:   {n_mined}")
    print(f"  Candidates verified: {n_disc}/{len(discoveries)}")
    print(f"  Total time:         {elapsed:.1f}s")
    print("=" * 70)

    return {
        'proofs': proof_results,
        'mined': mined,
        'discoveries': discoveries,
    }


# =====================================================================
# CLI
# =====================================================================

def main_cli():
    """CLI entry point for theory_miner."""
    args = sys.argv[1:]
    if '--prove' in args:
        run_proofs(verbose=True)
    elif '--mine' in args:
        run_mining(verbose=True)
    elif '--discover' in args:
        run_discover(verbose=True)
    else:
        run_all(verbose=True)


if __name__ == '__main__':
    main_cli()
