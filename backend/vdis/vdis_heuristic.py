"""
VDIS Track B1 - the object of study. Implements the DecisionHeuristic
protocol (backend.refsolver.heuristics) using the gyrovector state/update
rule pinned in the spec (S3), via backend.vdis.gyro_ops.

Phase 1 scope: only the degenerate configuration needed for the S4
degeneracy test (A=R, D=1, c->0, beta=0, lambda_tau=lambda_chi=0) is
exercised so far. The rotor/torsion channel (S3.4), multi-algebra
support (C/H), and the curvature bandit (S3.5) are Phase 2 - the
constructor accepts their parameters now so Phase 2 can fill in the
rotor update without changing this file's interface, but `beta`,
`lambda_tau`, `lambda_chi` are inert (asserted zero) until then.

State: per literal (not per variable - matches heap[lit] = VDIS(lit) in
S3.6), a tangent vector t_lit of dimension `dim` (= D * m; Phase 1 only
supports A=R so m=1 and dim=D), stored at the origin per the spec's own
"implementation detail" note (avoids exp/log round trips every bump;
the ball point V_lit = exp_0(t_lit) is materialized only when the
transport-target geometry requires it).
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
        decay_gamma: float = 1.0,
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

    def _score(self, lit: int) -> float:
        """VDIS(lit) per S3.6 with lambda_tau=lambda_chi=0 and Psi taken as
        the fixed unit vector e_0 (torsion channel is disabled in this
        configuration, so there is no learned global conflict direction
        yet - Phase 2 replaces this with the EMA-updated Psi)."""
        psi = np.zeros(self.dim)
        psi[0] = 1.0
        return float(np.dot(self.t[lit], psi))  # sigma is monotone -> ranks the same pre/post

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        # Delta_C = sum_{l in C} alpha_l * t_l  (S3.1), alpha_l = 1/|C| default
        alpha = 1.0 / len(learned)
        delta_c = np.zeros(self.dim)
        for lit in learned:
            delta_c = delta_c + alpha * self.t[lit]

        # Bump = gyrotransport step (S3.2), applied to every literal in the
        # learned clause using the *pre-bump* Delta_C computed above.
        for lit in learned:
            v_lit = exp_map_zero(self.t[lit], self.c)  # materialize ball point
            transported = parallel_transport_from_zero(v_lit, delta_c, self.c)
            new_v_lit = exp_map(v_lit, self.eta * transported, self.c)
            self.t[lit] = log_map_zero(new_v_lit, self.c)

    def on_assign(self, lit: int) -> None:
        self.saved_phase[abs(lit)] = lit > 0

    def on_unassign(self, lit: int) -> None:
        pass

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        best_var = -1
        best_score = -float("inf")
        for v in range(1, num_vars + 1):
            if value[v] is not None:
                continue
            s = max(self._score(v), self._score(-v))
            if s > best_score:
                best_score = s
                best_var = v
        return best_var if self._score(best_var) >= self._score(-best_var) else -best_var

    def decay(self) -> None:
        # Decay = Mobius scalar multiplication (S3.3): t <- gamma (x)_c t
        if self.decay_gamma == 1.0:
            return
        for lit in list(self.t.keys()):
            self.t[lit] = mobius_scalar_mul(self.decay_gamma, self.t[lit], self.c)
