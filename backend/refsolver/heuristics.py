"""
Pluggable decision heuristics for backend.refsolver.CDCLSolver.

Everything except the decision rule (propagation, clause learning,
restarts) is identical across heuristics in this package, so comparing
heuristics in isolation measures the decision rule's effect on search
quality (decisions/conflicts/propagations to solve) - see docs/vdis/
for the experimental protocol this supports.

Deliberate v1 simplification: all heuristics here pick via an O(n) scan
over variables rather than an indexed priority heap with lazy deletion.
Correctness and a clean, identical decision-quality comparison matter
more than wall-clock speed for this experiment (the whole point is that
Python is already ~10^3x slower than Kissat and that's fine); a heap
would add bug surface without changing what's being measured.
"""

from __future__ import annotations

import random
from typing import List, Optional, Protocol, Sequence


class DecisionHeuristic(Protocol):
    """pick() must return a literal (positive or negative int), not just
    a variable - phase selection is the heuristic's responsibility."""

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None: ...
    def on_assign(self, lit: int) -> None: ...
    def on_unassign(self, lit: int) -> None: ...
    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int: ...
    def decay(self) -> None: ...


class EVSIDSHeuristic:
    """Exponential VSIDS (MiniSat-style): every variable in a learned
    clause gets its score bumped by var_inc; var_inc itself grows every
    conflict (equivalent to decaying all scores, but avoiding an O(n)
    pass every conflict), with periodic rescaling to avoid float
    overflow. Phase saving: remembers each variable's last assigned
    polarity and reuses it as the default decision phase; unassigned
    variables default to the positive phase.
    """

    def __init__(self, num_vars: int, var_decay: float = 0.95, seed: int = 0):
        self.num_vars = num_vars
        self.score = [0.0] * (num_vars + 1)
        self.var_inc = 1.0
        self.var_decay = var_decay
        self.saved_phase = [True] * (num_vars + 1)
        self._rng = random.Random(seed)

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        for lit in learned:
            v = abs(lit)
            self.score[v] += self.var_inc
        if self.var_inc > 1e100:
            for i in range(len(self.score)):
                self.score[i] *= 1e-100
            self.var_inc *= 1e-100

    def on_assign(self, lit: int) -> None:
        self.saved_phase[abs(lit)] = lit > 0

    def on_unassign(self, lit: int) -> None:
        pass  # phase already captured at assignment time

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        best_var = -1
        best_score = -1.0
        for v in range(1, num_vars + 1):
            if value[v] is None and self.score[v] > best_score:
                best_score = self.score[v]
                best_var = v
        return best_var if self.saved_phase[best_var] else -best_var

    def decay(self) -> None:
        self.var_inc /= self.var_decay


class LRBHeuristic:
    """Learning Rate Branching (Liang et al. 2016), simplified: for each
    currently-assigned variable, track how many conflicts have occurred
    since it was assigned and how many of those conflicts it
    "participated" in (appeared in the resolution - approximated here as
    appearing in the learned clause or the conflicting clause). On
    unassignment (backtrack), fold participated/conflicts_since into an
    exponential moving average that becomes the decision score.
    """

    def __init__(self, num_vars: int, alpha: float = 0.4, alpha_min: float = 0.06, seed: int = 0):
        self.num_vars = num_vars
        self.score = [0.0] * (num_vars + 1)
        self.alpha = alpha
        self.alpha_min = alpha_min
        self.participated = [0] * (num_vars + 1)
        self.conflicts_since_assigned = [0] * (num_vars + 1)
        self.assigned_var: List[bool] = [False] * (num_vars + 1)
        self.saved_phase = [True] * (num_vars + 1)
        self._rng = random.Random(seed)
        self._total_conflicts = 0

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        self._total_conflicts += 1
        participants = {abs(l) for l in learned}
        for v in range(1, self.num_vars + 1):
            if self.assigned_var[v]:
                self.conflicts_since_assigned[v] += 1
                if v in participants:
                    self.participated[v] += 1
        if self.alpha > self.alpha_min:
            self.alpha -= 1e-6

    def on_assign(self, lit: int) -> None:
        v = abs(lit)
        self.assigned_var[v] = True
        self.participated[v] = 0
        self.conflicts_since_assigned[v] = 0
        self.saved_phase[v] = lit > 0

    def on_unassign(self, lit: int) -> None:
        v = abs(lit)
        if self.conflicts_since_assigned[v] > 0:
            r = self.participated[v] / self.conflicts_since_assigned[v]
            self.score[v] = (1 - self.alpha) * self.score[v] + self.alpha * r
        self.assigned_var[v] = False

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        best_var = -1
        best_score = -1.0
        for v in range(1, num_vars + 1):
            if value[v] is None and self.score[v] > best_score:
                best_score = self.score[v]
                best_var = v
        return best_var if self.saved_phase[best_var] else -best_var

    def decay(self) -> None:
        pass  # LRB's decay is the alpha anneal in on_conflict, not a separate step


class RandomHeuristic:
    """Sanity floor: uniformly random unassigned variable, random phase."""

    def __init__(self, num_vars: int, seed: int = 0):
        self.num_vars = num_vars
        self._rng = random.Random(seed)

    def on_conflict(self, learned: Sequence[int], lbd: int, trail: Sequence[int]) -> None:
        pass

    def on_assign(self, lit: int) -> None:
        pass

    def on_unassign(self, lit: int) -> None:
        pass

    def pick(self, num_vars: int, value: List[Optional[bool]]) -> int:
        unassigned = [v for v in range(1, num_vars + 1) if value[v] is None]
        v = self._rng.choice(unassigned)
        return v if self._rng.random() < 0.5 else -v

    def decay(self) -> None:
        pass
