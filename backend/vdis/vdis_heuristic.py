"""
VDIS Track B1 - the object of study. Implements the DecisionHeuristic
protocol (backend.refsolver.heuristics) using the gyrovector state/update
rule pinned in the spec (S3), via backend.vdis.gyro_ops.

Patch (this file, second pass): the S3.1 rule "Delta_C = sum_l alpha_l *
t_l" has an absorbing fixed point at t=0 (docs/vdis/PHASE_1.md) - proved
empirically, tangent state stayed exactly zero even after real conflicts.
Fix: axis 0 of the tangent space is reserved as the "infinitesimal
fossil" direction and always receives a FIXED unit contribution
(1.0) per conflict, independent of any literal's current state - a
hyperdimensional-infinitesimal decomposition where the scalar/real part
carries exactly the EVSIDS dynamic (see the exact-equivalence argument in
docs/vdis/PHASE_1_PATCH.md) and axes 1..D-1, present only for D>1, carry
the genuinely state-dependent "living field" contribution untouched by
this patch (still inert / Phase 2 scope while D=1).

Two more bugs fixed in the same pass, both needed for the degeneracy
claim and neither related to the absorbing fixed point:
  - pick() must rank VARIABLES by combined activity across both
    polarities (t_v[0] + t_(-v)[0]), matching EVSIDS's single
    per-variable score - not by comparing the two literals' individual
    scores against each other, which is a different selection rule.
  - phase (polarity) selection needs an explicit saved-phase mechanism
    (last assigned polarity), matching EVSIDSHeuristic, rather than
    "whichever literal's own score is higher" - a per-literal score
    comparison is not what phase-saving is and doesn't reduce to it.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np

from .gyro_ops import exp_map, exp_map_zero, log_map_zero, mobius_scalar_mul, parallel_transport_from_zero


class VDISHeuristic:
    def __init__(
        self,
        num_vars: int,
        dim: int = 1,
        c: float = 0.0,
        eta: float = 1.0,
        decay_gamma: float = 0.95,
        beta: float = 0.0,
        lambda_tau: float = 0.0,
        lambda_chi: float = 0.0,
        seed: int = 0,
    ):
        if beta != 0.0 or lambda_tau != 0.0 or lambda_chi != 0.0:
            raise NotImplementedError(
                "rotor/torsion channel (beta, lambda_tau, lambda_chi != 0) is "
                "Phase 2 scope; Phase 1 only implements the degenerate "
                "(beta=0, lambda_tau=0, lambda_chi=0) configuration needed "
                "for the S4 degeneracy test."
            )
        self.num_vars = num_vars
        self.dim = dim
        self.c = c
        self.eta = eta
        self.decay_gamma = decay_gamma
        self._rng = np.random.default_rng(seed)

        # Tangent state per literal, at the origin (t_lit = log_0^c(V_lit)).
        self.t: Dict[int, np.ndarray] = {}
        for v in range(1, num_vars + 1):
            self.t[v] = np.zeros(dim)
            self.t[-v] = np.zeros(dim)

        self.saved_phase = [True] * (num_vars + 1)

    def _var_activity(self, v: int) -> float:
        """Combined activity across both polarities of variable v, axis 0
        only (the fossil/EVSIDS-equivalent axis) - matches EVSIDS's single
        per-variable score, which accumulates regardless of which polarity
        of v appeared in a given learned clause."""
        return float(self.t[v][0] + self.t[-v][0])

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        alpha = 1.0 / len(learned)
        delta_c = np.zeros(self.dim)

        # Axis 0: fixed infinitesimal unit of conflict mass - a conflict
        # occurred and this literal participated, full stop, independent
        # of anyone's current state. This is what the degenerate (D=1)
        # case reduces to; it is NOT state-dependent, unlike axes 1..D-1.
        delta_c[0] = 1.0

        # Axes 1..D-1 (Phase 2 scope, inert while dim=1): the genuinely
        # state-dependent "living field" contribution from S3.1.
        if self.dim > 1:
            for lit in learned:
                delta_c[1:] += alpha * self.t[lit][1:]

        for lit in learned:
            v_lit = exp_map_zero(self.t[lit], self.c)
            transported = parallel_transport_from_zero(v_lit, delta_c, self.c)
            new_v_lit = exp_map(v_lit, self.eta * transported, self.c)
            self.t[lit] = log_map_zero(new_v_lit, self.c)

    def on_assign(self, lit: int) -> None:
        self.saved_phase[abs(lit)] = lit > 0

    def on_unassign(self, lit: int) -> None:
        pass

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        best_var = -1
        best_activity = -float("inf")
        for v in range(1, num_vars + 1):
            if value[v] is not None:
                continue
            a = self._var_activity(v)
            if a > best_activity:
                best_activity = a
                best_var = v
        return best_var if self.saved_phase[best_var] else -best_var

    def decay(self) -> None:
        # Decay = Mobius scalar multiplication (S3.3): t <- gamma (x)_c t,
        # applied to every literal's full state every conflict. At c=0
        # this is a direct rescale t *= gamma, which is exactly order-
        # equivalent (up to a positive global constant shared by every
        # literal at a given step) to EVSIDS's "grow var_inc instead of
        # decaying scores" implementation, provided decay_gamma ==
        # EVSIDSHeuristic's var_decay and eta == its initial var_inc -
        # see docs/vdis/PHASE_1_PATCH.md for the derivation.
        if self.decay_gamma == 1.0:
            return
        for lit in list(self.t.keys()):
            self.t[lit] = mobius_scalar_mul(self.decay_gamma, self.t[lit], self.c)
