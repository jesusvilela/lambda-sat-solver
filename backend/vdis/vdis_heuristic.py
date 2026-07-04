"""
VDIS Track B1 - the object of study. Implements the DecisionHeuristic
protocol (backend.refsolver.heuristics) using the gyrovector state/update
rule pinned in the spec (S3), via backend.vdis.gyro_ops and, for the
Phase 2 rotor/torsion channel, backend.vdis.algebra.

Phase 1 patch (kept): the S3.1 rule "Delta_C = sum_l alpha_l * t_l" has
an absorbing fixed point at t=0 (docs/vdis/PHASE_1.md) - proved
empirically. Fix: axis 0 of the tangent space is the "infinitesimal
fossil" direction and always receives a FIXED unit contribution (1.0)
per conflict, independent of any literal's current state; the scalar
part carries exactly the EVSIDS dynamic (docs/vdis/PHASE_1_PATCH.md;
gate accepted at float64 exactness by operator decision).

Phase 2 (docs/vdis/PHASE_2.md) adds, per the S3 spec:
  - Hypercomplex algebras A in {R, C, H}: dim = D * m real axes viewed
    as D slots of m = dim_R(A) coords each. Axis 0 (slot 0's scalar
    part) remains the fossil axis.
  - Living-field initialization: axes 1..dim-1 start at eps * N(0,1)
    (seeded). Without this the SAME absorbing-fixed-point argument that
    killed Phase 1's first attempt applies verbatim to the living axes:
    their forcing (S3.1) and the rotor wedge are both proportional to
    current state, so from exact zero they stay exactly zero forever.
    The spec's state decomposition (u_l on the unit sphere S^{Dm-1})
    presumes a direction exists; eps-init makes one. Axis 0's init
    stays exactly 0.0, so the fossil dynamic is untouched.
  - Rotor/torsion channel (S3.4): Omega_l += beta * (that_l ^ dhat_C)
    with vectors extracted per algebra.vector_part from normalized
    slot-sums; R_l = exp(Omega_l / 2); tau_l = <R_l Psi R_l', Psi>_0.
    Psi is a unit rotor updated as an EMA of the rotors exp(w/2),
    w = (previous conflict direction) ^ (current conflict direction).
    Omega decays by the same gamma as t (pinned choice - unspecified in
    S3.4; without it |Omega| grows ~beta per conflict without bound).
  - Decision scalar (S3.6): score(l) = <t_l, Psi>_Cl + lambda_tau*tau_l
    + lambda_chi*chi_l, with <t, Psi>_Cl = sum over slots of the
    Clifford inner product <slot_d Psi~>_0 = dot(slot_d, Psi). sigma is
    the identity (monotone, so ordering-equivalent to any sigmoid, and
    it cannot introduce new float64 ties the way a compressive sigma
    could). Variables are ranked by score(+v) + score(-v), phase by
    saved polarity - both carried over from the Phase 1 patch.
  - chi_l: precomputed per-literal clause-length statistic (see
    compute_chi) - 0 when no formula profile is supplied.

Degenerate-path guarantee: with algebra='R', dim=1, beta=0,
lambda_tau=lambda_chi=0 every arithmetic operation on the fossil axis
is float64-identical to the Phase 1 implementation (vectorized decay
multiplies elementwise by the same gamma; the bump chain is unchanged),
so the S4 degeneracy gate keeps holding - enforced by
test_vdis_degeneracy.py, not assumed.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence

import numpy as np

from .algebra import (
    algebra_dims,
    identity_rotor,
    rotor_exp,
    rotor_normalize,
    rotor_sandwich,
    vector_part,
    wedge,
)
from .gyro_ops import (
    exp_map,
    exp_map_zero,
    log_map_zero,
    parallel_transport_from_zero,
)

_TINY = 1e-12


def primes_up_to_nth(n: int) -> np.ndarray:
    """First n primes (simple sieve with a safe upper bound)."""
    if n == 0:
        return np.array([], dtype=int)
    # n-th prime < n(ln n + ln ln n) for n >= 6; pad generously below that
    bound = max(15, int(n * (np.log(n) + np.log(np.log(n)) + 1.2))) if n >= 6 else 15
    sieve = np.ones(bound + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(bound ** 0.5) + 1):
        if sieve[p]:
            sieve[p * p :: p] = False
    primes = np.flatnonzero(sieve)
    assert len(primes) >= n, "prime bound too small"
    return primes[:n]


def prime_anchor_bivectors(num_vars: int) -> np.ndarray:
    """VDIS v2 anchors (VDIS2_PREREG.md): variable v gets the fixed unit
    bivector (cos th_v, sin th_v, 0) with th_v = 2*pi*(p_v mod 360)/360,
    p_v the v-th prime; negative polarity is antipodal (th + pi).
    Prime spacing mod 360 spreads phases over the full circle with no
    collectively re-aligning arithmetic subfamily - deterministic,
    state-independent symmetry breaking for the rotor channel.
    Returns (2*num_vars+1, 3), indexed lit + num_vars."""
    theta = 2.0 * np.pi * (primes_up_to_nth(num_vars) % 360) / 360.0
    anchors = np.zeros((2 * num_vars + 1, 3))
    for v in range(1, num_vars + 1):
        t = theta[v - 1]
        anchors[v + num_vars] = (np.cos(t), np.sin(t), 0.0)
        anchors[-v + num_vars] = (np.cos(t + np.pi), np.sin(t + np.pi), 0.0)
    return anchors


def compute_chi(clauses: Sequence[Sequence[int]], num_vars: int) -> np.ndarray:
    """Per-literal chi (S3.6): 2 / (mean length of clauses containing the
    literal), in (0, 1] with 1 for all-binary neighborhoods, 0 for
    literals in no clause. Pinned simple version - the spec's
    "curvature-compatibility with kappa_f" is not given a formula, and
    inventing a kappa interaction here would be exactly the kind of
    unvalidated bridge the protocol parks; the kappa dependence enters
    only through which kappa the curvature bandit picks per family.
    Indexed by lit + num_vars (same layout as the heuristic's state)."""
    total_len = np.zeros(2 * num_vars + 1)
    count = np.zeros(2 * num_vars + 1)
    for clause in clauses:
        n = len(clause)
        for lit in clause:
            total_len[lit + num_vars] += n
            count[lit + num_vars] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        chi = np.where(count > 0, 2.0 * count / np.where(total_len > 0, total_len, 1.0), 0.0)
    return chi


class VDISHeuristic:
    def __init__(
        self,
        num_vars: int,
        dim: int = 1,
        c: float = 0.0,
        eta: float = 1.0,
        decay_gamma: float = 0.95,
        algebra: str = "R",
        beta: float = 0.0,
        lambda_tau: float = 0.0,
        lambda_chi: float = 0.0,
        psi_mu: float = 0.05,
        living_eps: float = 1e-3,
        chi: Optional[np.ndarray] = None,
        torsion_anchor: bool = False,
        wedge_ortho: bool = False,
        pair_torsion: float = 0.0,
        tie_break_pair: bool = False,
        moving_frame: bool = False,
        tie_break_frame: float = 0.0,
        combine_nudges: bool = False,
        nudge_gate: float = 1.0,
        combine_eta: float = 0.5,
        combine_traders: tuple = ("theta", "prime"),
        clauses: Optional[Sequence[Sequence[int]]] = None,
        community_labels: Optional[Sequence[int]] = None,
        breath_amp: float = 0.0,
        breath_rate: float = 0.05,
        seed: int = 0,
    ):
        m, bdim = algebra_dims(algebra)
        if dim % m != 0:
            raise ValueError(
                f"dim={dim} is not a multiple of dim_R({algebra!r})={m}"
            )
        if algebra == "R" and (beta != 0.0 or lambda_tau != 0.0):
            raise ValueError(
                "rotor/torsion channel needs a bivector structure; "
                "algebra 'R' has none (use 'C' or 'H')"
            )
        if dim > 64:
            raise ValueError("S3.7 hard budget: dim = D*m <= 64")

        self.num_vars = num_vars
        self.dim = dim
        self.c = c
        # Breathing curvature (hypercomplex_breathing.py): c oscillates
        # with conflict count, c(t) = c_base + amp*sin(rate*t), clamped
        # >= 0 (c is curvature magnitude). amp=0 disables (fixed c).
        self._c_base = c
        self.breath_amp = breath_amp
        self.breath_rate = breath_rate
        self._breath_t = 0
        self.eta = eta
        self.decay_gamma = decay_gamma
        self.algebra = algebra
        self.m = m
        self.D = dim // m
        self.beta = beta
        self.lambda_tau = lambda_tau
        self.lambda_chi = lambda_chi
        self.psi_mu = psi_mu
        self._rng = np.random.default_rng(seed)

        # Tangent state, one row per literal: row index = lit + num_vars
        # (row num_vars, "literal 0", is unused). self.t exposes dict-of-
        # views access; all mutation goes through the backing array so
        # views stay live and decay can be one vectorized multiply.
        self._t = np.zeros((2 * num_vars + 1, dim))
        if dim > 1 and living_eps > 0.0:
            self._t[:, 1:] = living_eps * self._rng.standard_normal(
                (2 * num_vars + 1, dim - 1)
            )
            self._t[num_vars, :] = 0.0
        self.t: Dict[int, np.ndarray] = {
            lit: self._t[lit + num_vars]
            for lit in range(-num_vars, num_vars + 1)
            if lit != 0
        }

        self.saved_phase = [True] * (num_vars + 1)

        # VDIS v2 (VDIS2_PREREG.md): prime-anchored 360-degree torsion
        # source and/or orthogonalized wedge. Anchors need the 3-dim
        # bivector space of H; ortho works for any rotor algebra.
        if torsion_anchor and algebra != "H":
            raise ValueError("torsion_anchor requires algebra 'H' (3-dim bivectors)")
        if (torsion_anchor or wedge_ortho) and beta == 0.0:
            raise ValueError("v2 torsion variants need beta != 0")
        self.torsion_anchor = torsion_anchor
        self.wedge_ortho = wedge_ortho
        self._anchors = prime_anchor_bivectors(num_vars) if torsion_anchor else None

        # VDIS v3 (VDIS3_PREREG.md): polarity-pair torsion - theta_v =
        # angle between the living-state directions of x and x' (the
        # operator's corrected reading of "primes ... in conjunction to
        # ortho"). Read directly from the pair: no Psi, no rotor, so
        # neither of the two measured v1/v2 death pathways applies.
        if (pair_torsion != 0.0 or tie_break_pair) and dim <= 1:
            raise ValueError("pair torsion needs living axes (dim > 1)")
        self.pair_torsion = pair_torsion
        self.tie_break_pair = tie_break_pair
        self.tie_breaks_fired = 0  # R1 liveness instrumentation

        # VDIS v6 (VDIS6_PREREG.md): online nudge-combiner. The surviving
        # nudges become experts; base (fossil axis-0) is the always-on
        # channelized core; theta and a static prime identity scalar are
        # Hedge-reweighted on LBD reward, scaled by an ascendency gate.
        self.combine_nudges = combine_nudges
        self.nudge_gate = nudge_gate
        self.combine_eta = combine_eta
        if combine_nudges:
            valid = {"theta", "prime", "lagrange", "centrality", "degree", "random", "gate"}
            if not combine_traders or set(combine_traders) - valid:
                raise ValueError(f"combine_traders must be a nonempty subset of {valid}")
            if "theta" in combine_traders and dim <= 1:
                raise ValueError("theta trader needs living axes (dim > 1)")
            if ("centrality" in combine_traders or "degree" in combine_traders) and clauses is None:
                raise ValueError("centrality/degree trader needs clauses= at construction")
            self._centrality = (
                self._eigenvector_centrality(clauses, num_vars)
                if "centrality" in combine_traders else None
            )
            # degree = raw variable occurrence count (the classical, non-
            # self-referential ablation of eigenvector centrality)
            if "degree" in combine_traders:
                deg = np.zeros(num_vars + 1)
                for cl in clauses:
                    for l in cl:
                        deg[abs(l)] += 1.0
                self._degree = deg
            # random static prior (information control: same shape, zero signal)
            if "random" in combine_traders:
                self._random_prior = self._rng.random(num_vars + 1)
                self._random_prior[0] = 0.0
            # gate / holographic-screen: how many distinct communities a
            # variable's clauses span (boundary/cut variables score high).
            # community_labels given = oracle; else detected by label prop.
            if "gate" in combine_traders:
                labels = (list(community_labels) if community_labels is not None
                          else self._detect_communities(clauses, num_vars))
                spans = [set() for _ in range(num_vars + 1)]
                for cl in clauses:
                    vs = [abs(l) for l in cl]
                    for v in vs:
                        for u in vs:
                            spans[v].add(labels[u])
                self._gate = np.array([len(s) for s in spans], dtype=float)
                self._gate[0] = 0.0
            self._traders = tuple(combine_traders)
            self._w = np.full(len(self._traders), 1.0 / len(self._traders))
            pr = primes_up_to_nth(num_vars)
            self._prime_scalar = np.zeros(num_vars + 1)
            self._prime_scalar[1:] = (pr % 360) / 360.0
            self._lam = np.zeros(num_vars + 1)  # Lagrange multipliers
            self._last_decision = -1
            self._last_endorse = np.zeros(len(self._traders))
            self._ema_lbd = None  # running LBD baseline for advantage reward
            self._lam_cycled = False  # Z0 instrumentation: saw a descent

        # VDIS v4 (VDIS4_PREREG.md): rotor restored in a Cartan moving
        # frame. F chases the conflict flow with body-frame (right)
        # composition - the "moving moving" scheme; per-literal Omega
        # accumulates FRAME-RELATIVE wedges, so the signal zero is
        # "co-rotating with the flow", not "aligned with Delta" (the
        # measured v1/v2 death mode). Readout: rho_v = |Omega_+v -
        # Omega_-v| (polarity disagreement, x/x' conjunction), fed to
        # the anti-ambiguous tie-break with weight tie_break_frame.
        if moving_frame and (algebra != "H" or beta == 0.0):
            raise ValueError("moving_frame needs algebra 'H' and beta != 0")
        if tie_break_frame != 0.0 and not moving_frame:
            raise ValueError("tie_break_frame needs moving_frame=True")
        self.moving_frame = moving_frame
        self.tie_break_frame = tie_break_frame
        if moving_frame:
            self._frame = identity_rotor(algebra)
            self._prev_dworld: Optional[np.ndarray] = None

        # Rotor channel state (only materialized when the algebra has
        # bivectors AND the channel can influence anything).
        self._rotor_active = bdim > 0 and beta != 0.0
        if bdim > 0:
            self._omega = np.zeros((2 * num_vars + 1, bdim))
            self._rotors = np.tile(identity_rotor(algebra), (2 * num_vars + 1, 1))
            self._rotors_dirty = False
            self.psi = identity_rotor(algebra)
            self._prev_dvec: Optional[np.ndarray] = None
        else:
            self.psi = identity_rotor("R") if algebra == "R" else None

        self._chi = chi
        if chi is not None and len(chi) != 2 * num_vars + 1:
            raise ValueError("chi must have length 2*num_vars + 1")

        # Full scoring engages whenever anything beyond the fossil-axis
        # activity can matter. The degenerate configuration keeps the
        # exact Phase 1 code path (see module docstring).
        self._full_scoring = (
            algebra != "R"
            or self.lambda_tau != 0.0
            or self.lambda_chi != 0.0
            or self.pair_torsion != 0.0
            or self.tie_break_pair
        )

    # -- helpers ----------------------------------------------------------

    def _var_activity(self, v: int) -> float:
        """Degenerate-path ranking: combined axis-0 activity across both
        polarities, matching EVSIDS's single per-variable score."""
        return float(self.t[v][0] + self.t[-v][0])

    def _unit_alg_vector(self, x: np.ndarray) -> Optional[np.ndarray]:
        """Normalized tangent -> slot-sum algebra element -> grade-1
        vector -> normalized; None when any stage is degenerate."""
        n = np.linalg.norm(x)
        if n <= _TINY:
            return None
        vec = vector_part((x / n).reshape(self.D, self.m).sum(axis=0), self.algebra)
        vn = np.linalg.norm(vec)
        if vn <= _TINY:
            return None
        return vec / vn

    def _to_frame(self, v: np.ndarray) -> np.ndarray:
        """Express a 3-vector in the moving frame: Im(F-conj (0,v) F)."""
        from .algebra import quat_mul, quat_conj
        q = np.concatenate([[0.0], v])
        return quat_mul(quat_mul(quat_conj(self._frame), q), self._frame)[1:]

    def _frame_rho(self) -> np.ndarray:
        """rho_v = |Omega_+v - Omega_-v| per variable (v4 readout):
        polarity disagreement of frame-relative accumulated torsion."""
        n = self.num_vars
        pos = self._omega[n + 1 :]
        neg = self._omega[n - 1 :: -1][:n]
        out = np.zeros(n + 1)
        out[1:] = np.linalg.norm(pos - neg, axis=1)
        return out

    def _pair_angles(self) -> np.ndarray:
        """theta_v in [0, pi] per variable (index 1..num_vars): angle
        between the two polarities' living-state directions (v3, pinned
        in VDIS3_PREREG.md). 0 where either side is degenerate."""
        n = self.num_vars
        norms = np.linalg.norm(self._t, axis=1, keepdims=True)
        safe = np.where(norms > _TINY, norms, 1.0)
        unit = self._t / safe
        # slot-sum -> algebra element -> vector part (imaginary coords for H)
        alg = unit.reshape(2 * n + 1, self.D, self.m).sum(axis=1)
        vec = alg[:, 1:] if self.algebra == "H" else alg
        vnorm = np.linalg.norm(vec, axis=1, keepdims=True)
        vunit = np.where(vnorm > _TINY, vec / np.where(vnorm > 0, vnorm, 1.0), 0.0)
        pos = vunit[n + 1 :]           # rows for +1..+n
        neg = vunit[n - 1 :: -1][:n]   # rows for -1..-n, aligned to +1..+n
        ok = (norms[n + 1 :, 0] > _TINY) & (norms[n - 1 :: -1][:n, 0] > _TINY)
        ok &= (vnorm[n + 1 :, 0] > _TINY) & (vnorm[n - 1 :: -1][:n, 0] > _TINY)
        raw_cross = np.cross(pos, neg)
        # np.cross returns (N,) scalars for 2-dim inputs (algebra C),
        # (N, 3) vectors for 3-dim (algebra H)
        cross = np.abs(raw_cross) if raw_cross.ndim == 1 else np.linalg.norm(raw_cross, axis=1)
        dot = np.sum(pos * neg, axis=1)
        theta = np.where(ok, np.arctan2(cross, dot), 0.0)
        out = np.zeros(self.num_vars + 1)
        out[1:] = theta
        return out

    def _lit_scores(self) -> np.ndarray:
        """S3.6 decision scalar for every literal (row layout)."""
        psi_tiled = np.tile(self.psi, self.D)
        scores = self._t @ psi_tiled
        if self.lambda_tau != 0.0:
            if self._rotors_dirty:
                self._rotors = rotor_exp(self._omega / 2.0, self.algebra)
                self._rotors_dirty = False
            sandwich = rotor_sandwich(self._rotors, self.psi, self.algebra)
            tau = np.sum(sandwich * self.psi, axis=-1)
            scores = scores + self.lambda_tau * tau
        if self.lambda_chi != 0.0 and self._chi is not None:
            scores = scores + self.lambda_chi * self._chi
        return scores

    # -- DecisionHeuristic protocol ----------------------------------------

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        if self.breath_amp != 0.0:
            self._breath_t += 1
            self.c = max(0.0, self._c_base + self.breath_amp * np.sin(self.breath_rate * self._breath_t))
        alpha = 1.0 / len(learned)
        delta_c = np.zeros(self.dim)

        # Axis 0: fixed infinitesimal unit of conflict mass - a conflict
        # occurred and this literal participated, full stop, independent
        # of anyone's current state (the Phase 1 patch; this is what the
        # degenerate D=1 case reduces to).
        delta_c[0] = 1.0

        # Axes 1..dim-1: the state-dependent "living field" from S3.1.
        if self.dim > 1:
            for lit in learned:
                delta_c[1:] += alpha * self.t[lit][1:]

        # v4 moving-frame rotor (VDIS4_PREREG.md) - replaces the fixed-
        # frame S3.4 accumulation entirely when active.
        if self._rotor_active and self.moving_frame:
            dvec = self._unit_alg_vector(delta_c)
            if dvec is not None:
                d_rel = self._to_frame(dvec)
                if self._prev_dworld is not None:
                    p_rel = self._to_frame(self._prev_dworld)
                    w = wedge(p_rel, d_rel, self.algebra)
                    # body-frame (right) composition: the frame update
                    # is expressed in the frame's own coordinates.
                    from .algebra import quat_mul
                    self._frame = rotor_normalize(
                        quat_mul(self._frame, rotor_exp(w / 2.0, self.algebra)),
                        self.algebra,
                    )
                    d_rel = self._to_frame(dvec)  # re-express in updated frame
                for lit in learned:
                    tvec = self._unit_alg_vector(self.t[lit])
                    if tvec is not None:
                        self._omega[lit + self.num_vars] += self.beta * wedge(
                            self._to_frame(tvec), d_rel, self.algebra
                        )
                    if self.torsion_anchor:
                        # v4-MF3: fixed prime-phase anchor, re-expressed
                        # in the moving frame - the anchor precesses
                        # with the conflict flow instead of being static.
                        self._omega[lit + self.num_vars] += (
                            self.beta
                            * self._to_frame(self._anchors[lit + self.num_vars])
                        )
                self._prev_dworld = dvec
        # Rotor/torsion channel (S3.4; v2 variants per VDIS2_PREREG.md).
        elif self._rotor_active:
            dvec = self._unit_alg_vector(delta_c)
            if dvec is not None:
                for lit in learned:
                    tvec = self._unit_alg_vector(self.t[lit])
                    if tvec is not None:
                        if self.wedge_ortho:
                            # v2 "360 orto": wedge from the renormalized
                            # orthogonal component - unit magnitude by
                            # construction, cannot align itself to death.
                            perp = tvec - float(np.dot(tvec, dvec)) * dvec
                            pn = np.linalg.norm(perp)
                            if pn > _TINY:
                                self._omega[lit + self.num_vars] += (
                                    self.beta * wedge(perp / pn, dvec, self.algebra)
                                )
                        else:
                            self._omega[lit + self.num_vars] += self.beta * wedge(
                                tvec, dvec, self.algebra
                            )
                    if self.torsion_anchor:
                        # v2 "360 + primes": fixed per-literal phase
                        # injection - the fossil-axis trick lifted to
                        # the rotor channel, state-independent.
                        self._omega[lit + self.num_vars] += (
                            self.beta * self._anchors[lit + self.num_vars]
                        )
                self._rotors_dirty = True
                if self.torsion_anchor:
                    # Psi = EMA of the learned clause's anchor signature:
                    # a running phase-record of WHICH variables conflict.
                    omega_c = np.mean(
                        [self._anchors[lit + self.num_vars] for lit in learned],
                        axis=0,
                    )
                    r_c = rotor_exp(omega_c / 2.0, self.algebra)
                    self.psi = rotor_normalize(
                        (1.0 - self.psi_mu) * self.psi + self.psi_mu * r_c,
                        self.algebra,
                    )
                elif self._prev_dvec is not None:
                    w = wedge(self._prev_dvec, dvec, self.algebra)
                    r_c = rotor_exp(w / 2.0, self.algebra)
                    self.psi = rotor_normalize(
                        (1.0 - self.psi_mu) * self.psi + self.psi_mu * r_c,
                        self.algebra,
                    )
                self._prev_dvec = dvec

        # Bump = gyrotransport step (S3.2), unchanged from Phase 1.
        for lit in learned:
            v_lit = exp_map_zero(self.t[lit], self.c)
            transported = parallel_transport_from_zero(v_lit, delta_c, self.c)
            new_v_lit = exp_map(v_lit, self.eta * transported, self.c)
            self.t[lit][:] = log_map_zero(new_v_lit, self.c)

        # v6 Hedge update (advantage-baselined - see VDIS6_PREREG.md
        # correction 1). Reward = normalized ADVANTAGE of this conflict's
        # LBD over the running-average LBD: positive when the endorsed
        # decision produced a tighter-than-typical (better) learned
        # clause, NEGATIVE when worse. Baselining is what stops the naive
        # r=1/lbd rule from self-saturating (a dominating trader endorses
        # its own picks and, with unconditionally-positive reward, runs
        # away regardless of quality - caught at the Y0 probe).
        if self.combine_nudges:
            # Lagrange dual ascent + relaxation decay (VDIS7): a variable
            # still being litigated in conflicts has its multiplier raised;
            # all multipliers decay (bounded). Descent-on-decision is in pick().
            if "lagrange" in self._traders:
                for lit in learned:
                    self._lam[abs(lit)] += 1.0
                self._lam *= 0.95
            if self._last_decision != -1:
                if self._ema_lbd is None:
                    self._ema_lbd = float(lbd)
                adv = (self._ema_lbd - lbd) / max(self._ema_lbd, 1.0)
                self._ema_lbd = 0.95 * self._ema_lbd + 0.05 * lbd
                self._w *= np.exp(self.combine_eta * adv * (self._last_endorse - 0.5))
                s = self._w.sum()
                if s > 0:
                    self._w /= s

    def on_assign(self, lit: int) -> None:
        self.saved_phase[abs(lit)] = lit > 0

    def on_unassign(self, lit: int) -> None:
        pass

    @staticmethod
    def _detect_communities(clauses, num_vars: int, iters: int = 20, seed: int = 0):
        """Label propagation on the variable co-occurrence graph — cheap
        unsupervised community detection (realistic; a solver does not
        know planted structure). Returns a label per variable."""
        from collections import defaultdict, Counter
        adj = defaultdict(list)
        for cl in clauses:
            vs = list({abs(l) for l in cl})
            for a in range(len(vs)):
                for b in range(a + 1, len(vs)):
                    adj[vs[a]].append(vs[b])
                    adj[vs[b]].append(vs[a])
        labels = list(range(num_vars + 1))
        rng = random.Random(seed)
        order = list(range(1, num_vars + 1))
        for _ in range(iters):
            rng.shuffle(order)
            changed = False
            for v in order:
                if not adj[v]:
                    continue
                cnt = Counter(labels[u] for u in adj[v])
                best = max(cnt.values())
                top = sorted(l for l, c in cnt.items() if c == best)
                if labels[v] not in top:
                    labels[v] = top[0]
                    changed = True
            if not changed:
                break
        return labels

    @staticmethod
    def _eigenvector_centrality(clauses, num_vars: int) -> np.ndarray:
        """Principal eigenvector of the variable co-occurrence graph
        A_ij = #clauses containing both i and j (VDIS8). The Godelian
        fixed point c_v proportional to sum_u A_vu c_u, by power
        iteration. Static structural prior, computed once. Returns a
        length num_vars+1 vector (index 0 unused)."""
        from collections import defaultdict
        adj = defaultdict(float)
        for cl in clauses:
            vs = list({abs(l) for l in cl})
            for a in range(len(vs)):
                for b in range(a + 1, len(vs)):
                    adj[(vs[a], vs[b])] += 1.0
                    adj[(vs[b], vs[a])] += 1.0
        c = np.ones(num_vars + 1)
        c[0] = 0.0
        for _ in range(100):
            nxt = np.zeros(num_vars + 1)
            for (i, j), w in adj.items():
                nxt[i] += w * c[j]
            n = np.linalg.norm(nxt)
            if n < 1e-15:
                break  # empty graph -> uniform (stays ones)
            nxt /= n
            if np.linalg.norm(nxt - c) < 1e-8:
                c = nxt
                break
            c = nxt
        c[0] = 0.0
        return c

    def _trader_score(self, name: str) -> np.ndarray:
        """Per-variable score vector for a named trader, in [0,1]."""
        if name == "theta":
            return self._pair_angles() / np.pi
        if name == "prime":
            return self._prime_scalar
        if name == "lagrange":
            # min-max normalized multiplier
            lam = self._lam.copy()
            lo, hi = lam[1:].min(), lam[1:].max()
            out = (lam - lo) / (hi - lo) if hi > lo else np.zeros_like(lam)
            out[0] = 0.0
            return out
        if name in ("centrality", "degree", "random", "gate"):
            c = {"centrality": self._centrality, "degree": getattr(self, "_degree", None),
                 "random": getattr(self, "_random_prior", None),
                 "gate": getattr(self, "_gate", None)}[name]
            lo, hi = c[1:].min(), c[1:].max()
            out = (c - lo) / (hi - lo) if hi > lo else np.zeros_like(c)
            out[0] = 0.0
            return out
        raise ValueError(name)

    def _combiner_pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        # base = min-max-normalized fossil activity over unassigned vars
        act = np.full(self.num_vars + 1, -np.inf)
        for v in range(1, num_vars + 1):
            if value[v] is None:
                act[v] = self.t[v][0] + self.t[-v][0]
        finite = act[np.isfinite(act)]
        if finite.size == 0:
            return -1
        lo, hi = finite.min(), finite.max()
        base = np.where(np.isfinite(act), (act - lo) / (hi - lo) if hi > lo else 0.0, -np.inf)
        scores = [self._trader_score(t) for t in self._traders]
        combined = base + self.nudge_gate * sum(
            self._w[k] * scores[k] for k in range(len(self._traders))
        )
        combined[~np.isfinite(act)] = -np.inf
        best_var = int(np.argmax(combined[1:])) + 1
        self._last_decision = best_var
        self._last_endorse = np.array([float(s[best_var]) for s in scores])
        # Lagrange dual descent: committing to a variable pays down its
        # multiplier (the distinguishing primal-coupling; see VDIS7).
        if "lagrange" in self._traders and self._lam[best_var] > 0:
            self._lam[best_var] *= 0.5
            self._lam_cycled = True
        return best_var if self.saved_phase[best_var] else -best_var

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        if self.combine_nudges:
            return self._combiner_pick(num_vars, value)
        best_var = -1
        best_activity = -float("inf")
        if self._full_scoring:
            scores = self._lit_scores()
            tie_active = self.tie_break_pair or self.tie_break_frame != 0.0
            theta = (
                self._pair_angles()
                if (self.pair_torsion != 0.0 or self.tie_break_pair)
                else None
            )
            for v in range(1, num_vars + 1):
                if value[v] is not None:
                    continue
                a = scores[v + self.num_vars] + scores[-v + self.num_vars]
                if self.pair_torsion != 0.0:
                    a += self.pair_torsion * (theta[v] / np.pi)
                if a > best_activity:
                    best_activity = a
                    best_var = v
            if tie_active and best_var != -1:
                # Anti-ambiguous injection (v3/v4): within the near-tie
                # band the variable with the largest tie scalar wins -
                # pair angle (v3), frame-torsion polarity disagreement
                # (v4), or their sum. Clear decisions untouched.
                tie = np.zeros(self.num_vars + 1)
                if self.tie_break_pair:
                    tie += theta / np.pi
                if self.tie_break_frame != 0.0:
                    tie += self.tie_break_frame * self._frame_rho()
                band = best_activity - 1e-6 * max(abs(best_activity), 1.0)
                tied_best, tied_score = best_var, tie[best_var]
                n_tied = 1
                for v in range(1, num_vars + 1):
                    if v == best_var or value[v] is not None:
                        continue
                    a = scores[v + self.num_vars] + scores[-v + self.num_vars]
                    if self.pair_torsion != 0.0:
                        a += self.pair_torsion * (theta[v] / np.pi)
                    if a >= band:
                        n_tied += 1
                        if tie[v] > tied_score:
                            tied_best, tied_score = v, tie[v]
                if n_tied > 1 and tied_best != best_var:
                    self.tie_breaks_fired += 1
                    best_var = tied_best
        else:
            for v in range(1, num_vars + 1):
                if value[v] is not None:
                    continue
                a = self._var_activity(v)
                if a > best_activity:
                    best_activity = a
                    best_var = v
        return best_var if self.saved_phase[best_var] else -best_var

    def decay(self) -> None:
        # Decay = Mobius scalar multiplication (S3.3): t <- gamma (x)_c t.
        # At c=0 this is elementwise t *= gamma - bit-identical to the
        # Phase 1 per-literal mobius_scalar_mul(gamma, t, 0) = gamma * t,
        # which is what keeps the degeneracy gate green (verified by
        # test_vdis_degeneracy.py, not assumed). For c>0 the same map is
        # applied row-vectorized: tanh(gamma * artanh(sqrt(c)|t|)) along
        # each t's own direction.
        if self.decay_gamma == 1.0:
            return
        if self.c <= 0:
            self._t *= self.decay_gamma
        else:
            sqrt_c = np.sqrt(self.c)
            norms = np.linalg.norm(self._t, axis=1, keepdims=True)
            arg = np.clip(sqrt_c * norms, 0.0, 1.0 - 1e-15)
            with np.errstate(invalid="ignore", divide="ignore"):
                scale = np.where(
                    norms > _TINY,
                    np.tanh(self.decay_gamma * np.arctanh(arg))
                    / (sqrt_c * np.where(norms > 0, norms, 1.0)),
                    0.0,
                )
            self._t *= scale
        # Pinned choice: the rotor memory decays with the same gamma so
        # |Omega| stays bounded by ~beta/(1-gamma) (S3.4 doesn't specify
        # a decay; without one the bivector grows without bound and the
        # rotor angle aliases mod 2*pi).
        if self._rotor_active:
            self._omega *= self.decay_gamma
            self._rotors_dirty = True
