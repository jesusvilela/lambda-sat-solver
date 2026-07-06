"""
Reference CDCL solver (backend.refsolver).

Purpose: an instrumentable, pure-Python CDCL solver with a pluggable
decision-heuristic interface (see heuristics.py), so heuristics can be
compared on identical propagation/learning/restart machinery - isolating
the decision rule's effect on search quality. See docs/vdis/ for the
experimental protocol this exists to support.

Not a performance solver: Kissat is roughly 10^3x faster and is
unaffected by anything here. The metric of interest is search quality
(decisions/conflicts/propagations to solve a fixed instance), not
wall-clock time.

Algorithm: 2-watched-literal unit propagation, 1UIP conflict analysis
and clause learning, non-chronological backtracking, Luby restarts,
phase saving (delegated to the heuristic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..cnf_utils import CNFFormula
from .heuristics import DecisionHeuristic


class SolveResult(Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    UNKNOWN = "UNKNOWN"  # budget exhausted before a decision


@dataclass
class SolveStats:
    decisions: int = 0
    conflicts: int = 0
    propagations: int = 0
    restarts: int = 0
    learned_clauses: int = 0


def luby(i: int) -> int:
    """Luby restart sequence, 0-indexed: 1,1,2,1,1,2,4,1,1,2,1,1,2,4,8,..."""
    k = 1
    while (1 << k) - 1 < i + 1:
        k += 1
    if i + 1 == (1 << k) - 1:
        return 1 << (k - 1)
    return luby(i - ((1 << (k - 1)) - 1))


class CDCLSolver:
    def __init__(
        self,
        formula: CNFFormula,
        heuristic: DecisionHeuristic,
        max_conflicts: Optional[int] = None,
        luby_unit: int = 100,
    ):
        self.num_vars = formula.num_vars
        self.heuristic = heuristic
        self.max_conflicts = max_conflicts
        self.luby_unit = luby_unit

        self.clauses: List[List[int]] = []
        self.watches: Dict[int, List[int]] = {}
        for v in range(1, self.num_vars + 1):
            self.watches[v] = []
            self.watches[-v] = []

        self.value: List[Optional[bool]] = [None] * (self.num_vars + 1)
        self.level: List[int] = [0] * (self.num_vars + 1)
        self.reason: List[Optional[int]] = [None] * (self.num_vars + 1)
        self.trail: List[int] = []
        self.trail_lim: List[int] = []
        self.prop_head = 0
        self._unsat_at_level_0 = False

        self.stats = SolveStats()
        self._conflicts_since_restart = 0
        self._restart_index = 0

        for clause in formula.clauses:
            deduped = list(dict.fromkeys(clause))
            if len(deduped) == 0:
                self._unsat_at_level_0 = True
                continue
            idx = self._add_clause(deduped)
            if idx is not None and len(deduped) == 1:
                lit = deduped[0]
                existing = self._lit_value(lit)
                if existing is False:
                    self._unsat_at_level_0 = True
                elif existing is None:
                    self._enqueue(lit, reason=idx)

    # ---- clause management ----

    def _add_clause(self, lits: List[int]) -> Optional[int]:
        """Add a clause; return its index, or None if it's a tautology
        (dropped - tautologies are always satisfied and add nothing)."""
        litset = set(lits)
        for l in lits:
            if -l in litset:
                return None
        idx = len(self.clauses)
        self.clauses.append(lits)
        if len(lits) >= 2:
            self.watches[lits[0]].append(idx)
            self.watches[lits[1]].append(idx)
        return idx

    @property
    def decision_level(self) -> int:
        return len(self.trail_lim)

    # ---- assignment ----

    def _lit_value(self, lit: int) -> Optional[bool]:
        v = self.value[abs(lit)]
        if v is None:
            return None
        return v if lit > 0 else (not v)

    def _enqueue(self, lit: int, reason: Optional[int]) -> None:
        v = abs(lit)
        self.value[v] = lit > 0
        self.level[v] = self.decision_level
        self.reason[v] = reason
        self.trail.append(lit)
        self.heuristic.on_assign(lit)

    def _unassign(self, lit: int) -> None:
        v = abs(lit)
        self.value[v] = None
        self.reason[v] = None
        self.heuristic.on_unassign(lit)

    # ---- propagation (2-watched literals) ----

    def _propagate(self) -> Optional[int]:
        """Unit-propagate; return the index of a falsified clause on
        conflict, or None once the queue drains with no conflict."""
        while self.prop_head < len(self.trail):
            lit = self.trail[self.prop_head]
            self.prop_head += 1
            self.stats.propagations += 1
            false_lit = -lit
            watch_list = self.watches[false_lit]
            new_watch_list: List[int] = []
            i = 0
            conflict: Optional[int] = None
            while i < len(watch_list):
                clause_idx = watch_list[i]
                i += 1
                clause = self.clauses[clause_idx]
                if clause[0] == false_lit:
                    clause[0], clause[1] = clause[1], clause[0]
                other = clause[0]
                if self._lit_value(other) is True:
                    new_watch_list.append(clause_idx)
                    continue
                replaced = False
                for k in range(2, len(clause)):
                    cand = clause[k]
                    if self._lit_value(cand) is not False:
                        clause[1], clause[k] = clause[k], clause[1]
                        self.watches[clause[1]].append(clause_idx)
                        replaced = True
                        break
                if replaced:
                    continue
                new_watch_list.append(clause_idx)
                if self._lit_value(other) is False:
                    conflict = clause_idx
                    new_watch_list.extend(watch_list[i:])
                    break
                else:
                    self._enqueue(other, clause_idx)
            self.watches[false_lit] = new_watch_list
            if conflict is not None:
                return conflict
        return None

    # ---- conflict analysis (1UIP) ----

    def _analyze(self, conflict_idx: int) -> Tuple[List[int], int, int]:
        seen = [False] * (self.num_vars + 1)
        learned: List[int] = []
        lbd_levels = set()
        counter = 0
        trail_idx = len(self.trail) - 1
        p: Optional[int] = None
        reason_idx = conflict_idx

        while True:
            clause = self.clauses[reason_idx]
            for lit in clause:
                v = abs(lit)
                if p is not None and v == abs(p):
                    continue
                if seen[v] or self.level[v] == 0:
                    continue
                seen[v] = True
                if self.level[v] == self.decision_level:
                    counter += 1
                else:
                    learned.append(lit)
                    lbd_levels.add(self.level[v])
            while not seen[abs(self.trail[trail_idx])]:
                trail_idx -= 1
            p = self.trail[trail_idx]
            seen[abs(p)] = False
            trail_idx -= 1
            counter -= 1
            if counter == 0:
                break
            reason_idx = self.reason[abs(p)]

        asserting_lit = -p
        learned = [asserting_lit] + learned
        lbd_levels.add(self.decision_level)
        lbd = len(lbd_levels)
        backtrack_level = 0 if len(learned) == 1 else max(self.level[abs(l)] for l in learned[1:])
        return learned, backtrack_level, lbd

    def _backtrack(self, level: int) -> None:
        if self.decision_level <= level:
            return
        cut = self.trail_lim[level]
        for i in range(len(self.trail) - 1, cut - 1, -1):
            self._unassign(self.trail[i])
        del self.trail[cut:]
        del self.trail_lim[level:]
        self.prop_head = min(self.prop_head, len(self.trail))

    def _decide(self) -> None:
        self.trail_lim.append(len(self.trail))
        lit = self.heuristic.pick(self.num_vars, self.value)
        self.stats.decisions += 1
        self._enqueue(lit, reason=None)

    # ---- top-level solve loop ----

    def solve(self) -> Tuple[SolveResult, Optional[Dict[int, bool]]]:
        if self._unsat_at_level_0:
            return SolveResult.UNSAT, None

        conflict = self._propagate()
        if conflict is not None:
            return SolveResult.UNSAT, None

        conflicts_until_restart = self.luby_unit * luby(self._restart_index)

        while True:
            conflict = self._propagate()
            if conflict is not None:
                self.stats.conflicts += 1
                if self.decision_level == 0:
                    return SolveResult.UNSAT, None

                learned, backtrack_level, lbd = self._analyze(conflict)
                self._backtrack(backtrack_level)
                new_idx = self._add_clause(learned)
                assert new_idx is not None, "1UIP-learned clause was a tautology (bug)"
                self.stats.learned_clauses += 1
                self._enqueue(learned[0], reason=new_idx)

                self.heuristic.on_conflict(learned, lbd, self.trail)
                self.heuristic.decay()

                self._conflicts_since_restart += 1
                if self._conflicts_since_restart >= conflicts_until_restart:
                    self._backtrack(0)
                    self._conflicts_since_restart = 0
                    self._restart_index += 1
                    self.stats.restarts += 1
                    conflicts_until_restart = self.luby_unit * luby(self._restart_index)

                if self.max_conflicts is not None and self.stats.conflicts >= self.max_conflicts:
                    return SolveResult.UNKNOWN, None
            else:
                if all(self.value[v] is not None for v in range(1, self.num_vars + 1)):
                    model = {v: bool(self.value[v]) for v in range(1, self.num_vars + 1)}
                    return SolveResult.SAT, model
                self._decide()
