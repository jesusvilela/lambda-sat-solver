"""Finite, experimental ETH x Kakeya incidence probe for CNF formulas.

The clauses define a violation map v : {0,1}^n -> {0,1}^m.
Every CNF model has v=0 and therefore passes every homogeneous parity
check <a,v>=0 over GF(2). A set of parity rows is an *over-approximation*
of the original model set unless its kernel has no realizable nonzero
violation vector. In particular, passing the checks is NEVER a SAT proof.

The Kakeya-inspired incidence sets below are *finite subsets of Boolean
assignments*, not Euclidean tubes. Their Gram spectrum is a diagnostic,
not a transfer of a Kakeya maximal inequality, complexity bound or proof.
All audits enumerate assignments and are bounded by MAX_ENUM_VARS.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import chain, combinations
from math import sqrt
from random import Random
from typing import Sequence

from .cnf_utils import CNFFormula

MAX_ENUM_VARS = 12
MAX_CLAUSES = 128


def _check_formula(formula: CNFFormula, max_vars: int) -> None:
    if not 0 <= max_vars <= MAX_ENUM_VARS:
        raise ValueError(f"max_vars must be between 0 and {MAX_ENUM_VARS}")
    if not isinstance(formula.num_vars, int) or not 0 <= formula.num_vars <= max_vars:
        raise ValueError("formula exceeds explicit assignment-enumeration budget")
    if len(formula.clauses) > MAX_CLAUSES:
        raise ValueError("formula exceeds clause budget")
    for clause in formula.clauses:
        for literal in clause:
            if (not isinstance(literal, int) or isinstance(literal, bool)
                    or literal == 0 or abs(literal) > formula.num_vars):
                raise ValueError(f"invalid literal in CNF: {literal!r}")


def violation_masks(formula: CNFFormula, *, max_vars: int = 10) -> tuple[int, ...]:
    """Enumerate v_F(x), with assignment bit i encoding variable i+1.

    Bit j of the returned mask is 1 iff clause j is violated. A zero mask
    identifies a model. Declared but unused variables are still enumerated.
    """
    _check_formula(formula, max_vars)
    masks = []
    for assignment in range(1 << formula.num_vars):
        v = 0
        for i, clause in enumerate(formula.clauses):
            if not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause):
                v |= 1 << i
        masks.append(v)
    return tuple(masks)


def _check_rows(rows: Sequence[int], clause_count: int) -> None:
    if not 0 <= clause_count <= MAX_CLAUSES:
        raise ValueError("invalid clause count")
    for row in rows:
        if not isinstance(row, int) or isinstance(row, bool) or not 0 < row < (1 << clause_count):
            raise ValueError(f"invalid parity row: {row!r}")


def parity_accepts(violation: int, row: int) -> bool:
    """Does the homogeneous GF(2) check <row, violation> = 0 hold?"""
    if violation < 0 or row < 0:
        raise ValueError("bitmasks must be nonnegative")
    return ((violation & row).bit_count() & 1) == 0


@dataclass(frozen=True)
class HashAudit:
    models: int
    spurious: int

    @property
    def survivors(self) -> int:
        return self.models + self.spurious

    @property
    def equivalent_on_enumerated_domain(self) -> bool:
        return self.spurious == 0


def audit_hash(masks: Sequence[int], rows: Sequence[int], clause_count: int) -> HashAudit:
    """Exact finite audit, not a scalable verifier or a SAT certificate."""
    _check_rows(rows, clause_count)
    if any(mask < 0 or mask >= (1 << clause_count) for mask in masks):
        raise ValueError("violation mask out of clause domain")
    models = sum(v == 0 for v in masks)
    spurious = sum(v != 0 and all(parity_accepts(v, row) for row in rows)
                   for v in masks)
    return HashAudit(models, spurious)


def _candidate_rows(clause_count: int, max_weight: int,
                    budget: int, seed: int) -> tuple[int, ...]:
    """Include every singleton then reservoir-sample pairs/triples.

    This is a deliberately finite candidate search, NOT the expander-code /
    deterministic exact-counting construction of the ETH manuscript.
    """
    if not 0 <= clause_count <= MAX_CLAUSES:
        raise ValueError("invalid clause count")
    if budget < clause_count or budget > 8192:
        raise ValueError("candidate budget must be within [clause_count, 8192]")
    if max_weight < 1 or max_weight > 3:
        raise ValueError("max_weight must be in [1, 3]")
    singles = [1 << j for j in range(clause_count)]
    capacity = budget - len(singles)
    rng = Random(seed)
    sampled: list[int] = []
    if capacity > 0:
        combos = chain.from_iterable(combinations(range(clause_count), weight)
                                     for weight in range(2, min(max_weight, clause_count) + 1))
        for index, combo in enumerate(combos):
            row = sum(1 << j for j in combo)
            if index < capacity:
                sampled.append(row)
            else:
                slot = rng.randrange(index + 1)
                if slot < capacity:
                    sampled[slot] = row
    return tuple(sorted(singles + sampled, key=lambda row: (row.bit_count(), row)))


def greedy_violation_rows(training_masks: Sequence[int], clause_count: int, *,
                          max_rows: int = 8, max_weight: int = 3,
                          candidate_budget: int = 512,
                          candidate_seed: int = 0) -> tuple[int, ...]:
    """Greedily reject observed nonzero violation masks, weighted by frequency.

    This is a supervised small-n *diagnostic*. Since it sees training assignments,
    it must not be presented as a cheap dispatch feature or proof of an asymptotic
    improvement. Rows are a relaxation on out-of-sample assignments.
    """
    if not 0 <= clause_count <= MAX_CLAUSES:
        raise ValueError("invalid clause count")
    if not 0 <= max_rows <= 32:
        raise ValueError("max_rows must be in [0, 32]")
    if any(mask < 0 or mask >= (1 << clause_count) for mask in training_masks):
        raise ValueError("violation mask out of clause domain")
    candidates = _candidate_rows(clause_count, max_weight, candidate_budget,
                                 candidate_seed)
    remaining = Counter(v for v in training_masks if v)
    selected: list[int] = []
    for _ in range(max_rows):
        if not remaining:
            break
        winner = 0
        best_gain = 0
        for row in candidates:
            if row in selected:
                continue
            gain = sum(count for v, count in remaining.items()
                       if not parity_accepts(v, row))
            if gain > best_gain:
                winner, best_gain = row, gain
        if not winner:
            break
        selected.append(winner)
        remaining = Counter({v: count for v, count in remaining.items()
                             if parity_accepts(v, winner)})
    return tuple(selected)


def matched_random_rows(rows: Sequence[int], clause_count: int, seed: int) -> tuple[int, ...]:
    """Null control: same number of checks and identical row-weight sequence."""
    _check_rows(rows, clause_count)
    rng = Random(seed)
    return tuple(sum(1 << j for j in rng.sample(range(clause_count), row.bit_count()))
                 for row in rows)


@dataclass(frozen=True)
class IncidenceOverlap:
    active_rows: int
    top_gram_eigenvalue: float
    mean_pairwise_cosine: float
    maximum_multiplicity: int


def _top_eigenvalue(gram: list[list[float]]) -> float:
    """Power iteration for a symmetric, entrywise nonnegative Gram matrix."""
    n = len(gram)
    if n == 0:
        return 0.0
    v = [1.0 / sqrt(n)] * n
    last = 0.0
    for _ in range(300):
        w = [sum(gram[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = sqrt(sum(x * x for x in w))
        if norm == 0:
            return 0.0
        v = [x / norm for x in w]
        eig = sum(v[i] * sum(gram[i][j] * v[j] for j in range(n))
                  for i in range(n))
        if abs(eig - last) < 1e-12:
            return eig
        last = eig
    return last


def incidence_overlap(masks: Sequence[int], rows: Sequence[int],
                      clause_count: int) -> IncidenceOverlap:
    """Normalized Gram spectrum of parity-check pass sets on NON-models only.

    T_row = {x: v_F(x) != 0 and <row,v_F(x)> = 0}. Columns are finite
    assignment states, not Euclidean tubes. G[i,j] = |Ti intersect Tj| /
    sqrt(|Ti| |Tj|). This does not inherit any Kakeya inequality.
    """
    _check_rows(rows, clause_count)
    if len(rows) > 64:
        raise ValueError("incidence overlap supports at most 64 rows")
    if any(v < 0 or v >= (1 << clause_count) for v in masks):
        raise ValueError("violation mask out of clause domain")
    sets = [frozenset(i for i, v in enumerate(masks)
                      if v and parity_accepts(v, row)) for row in rows]
    active = [s for s in sets if s]
    k = len(active)
    if k == 0:
        return IncidenceOverlap(0, 0.0, 0.0, 0)
    gram = [[len(active[i] & active[j]) / sqrt(len(active[i]) * len(active[j]))
             for j in range(k)] for i in range(k)]
    cosines = [gram[i][j] for i in range(k) for j in range(i + 1, k)]
    nonmodels = [i for i, v in enumerate(masks) if v]
    maximum = max((sum(i in s for s in active) for i in nonmodels), default=0)
    return IncidenceOverlap(k, _top_eigenvalue(gram),
                            sum(cosines) / len(cosines) if cosines else 0.0,
                            maximum)


@dataclass(frozen=True)
class MatchedControl:
    seed: int
    rows: tuple[int, ...]
    heldout_spurious: int
    overlap: IncidenceOverlap


@dataclass(frozen=True)
class BridgeReport:
    variables: int
    clauses: int
    states: int
    models: int
    training_states: int
    heldout_states: int
    chosen_rows: tuple[int, ...]
    singleton_baseline_rows: tuple[int, ...]
    singleton_heldout_spurious: int
    singleton_overlap: IncidenceOverlap
    training_spurious: int
    heldout_spurious: int
    exact_audit: HashAudit
    overlap: IncidenceOverlap
    controls: tuple[MatchedControl, ...]


def run_bridge_experiment(formula: CNFFormula, *, max_vars: int = 10,
                          split_seed: int = 41, candidate_seed: int = 19,
                          max_rows: int = 8, max_weight: int = 3,
                          candidate_budget: int = 512,
                          control_seeds: Sequence[int] = (13, 29, 47, 71)) -> BridgeReport:
    """Train/holdout pilot with matched check-weight nulls; no solver verdicts.

    The full audit is only a finite-n consistency oracle; the heldout count
    measures generalization of a row set fitted on a different assignment set.
    """
    if len(control_seeds) > 64:
        raise ValueError("too many matched controls")
    masks = violation_masks(formula, max_vars=max_vars)
    indices = list(range(len(masks)))
    Random(split_seed).shuffle(indices)
    train_n = min(len(indices), max(1, (2 * len(indices)) // 3))
    if len(indices) > 1:
        train_n = min(train_n, len(indices) - 1)
    training = tuple(masks[i] for i in indices[:train_n])
    heldout = tuple(masks[i] for i in indices[train_n:])
    chosen = greedy_violation_rows(training, len(formula.clauses),
                                   max_rows=max_rows, max_weight=max_weight,
                                   candidate_budget=candidate_budget,
                                   candidate_seed=candidate_seed)
    singleton = greedy_violation_rows(training, len(formula.clauses),
                                      max_rows=len(chosen), max_weight=1,
                                      candidate_budget=max(1, len(formula.clauses)))
    controls = []
    for seed in control_seeds:
        random_rows = matched_random_rows(chosen, len(formula.clauses), seed)
        controls.append(MatchedControl(seed, random_rows,
                       audit_hash(heldout, random_rows, len(formula.clauses)).spurious,
                       incidence_overlap(masks, random_rows, len(formula.clauses))))
    whole = audit_hash(masks, chosen, len(formula.clauses))
    return BridgeReport(
        variables=formula.num_vars, clauses=len(formula.clauses),
        states=len(masks), models=whole.models,
        training_states=len(training), heldout_states=len(heldout),
        chosen_rows=chosen,
        singleton_baseline_rows=singleton,
        singleton_heldout_spurious=audit_hash(heldout, singleton, len(formula.clauses)).spurious,
        singleton_overlap=incidence_overlap(masks, singleton, len(formula.clauses)),
        training_spurious=audit_hash(training, chosen, len(formula.clauses)).spurious,
        heldout_spurious=audit_hash(heldout, chosen, len(formula.clauses)).spurious,
        exact_audit=whole,
        overlap=incidence_overlap(masks, chosen, len(formula.clauses)),
        controls=tuple(controls),
    )
