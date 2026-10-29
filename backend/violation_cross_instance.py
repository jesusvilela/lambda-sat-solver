"""Instance-held-out pilot: does finite violation incidence predict DPLL effort?

This module never returns SAT/UNSAT decisions. The geometry is a diagnostic,
not Euclidean Kakeya geometry and not a consequence of either OpenAI theorem.
Unlike violation_geometry.violation_masks, its extraction samples bounded
assignments; the exact DPLL cost is calculated independently as an *outcome*.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from math import log2, sqrt
from random import Random
from time import perf_counter_ns
from typing import Sequence

import numpy as np

from .cnf_utils import CNFFormula
from .violation_spectral_null import centered_incidence
from .violation_geometry import (
    MAX_ENUM_VARS, _check_formula, greedy_violation_rows,
    incidence_overlap, matched_random_rows, parity_accepts,
)

FAMILIES = ("random-2SAT", "random-3SAT", "planted-3SAT",
            "random-3XOR", "tseitin", "pigeonhole")
STRUCTURAL = ("n", "m_over_n", "mean_width", "binary_fraction", "unit_fraction",
              "max_occurrence_over_n", "occurrence_cv", "polarity_imbalance",
              "xor_pattern_fraction")
SAMPLED = ("mean_violated_fraction", "std_violated_fraction", "sampled_model_fraction",
           "unique_violation_fraction")
LEARNED = ("learned_rejection_fraction", "learned_gram_top", "learned_gram_cosine",
           "learned_max_multiplicity_fraction")
NULL = ("null_rejection_fraction", "null_gram_top", "null_gram_cosine",
        "null_max_multiplicity_fraction")
CENTERED = ("centered_gram_top", "centered_mean_abs_correlation",
            "centered_triangle_frustration", "centered_triangle_mass")
CENTERED_NULL = ("null_centered_gram_top", "null_centered_mean_abs_correlation",
                 "null_centered_triangle_frustration", "null_centered_triangle_mass")
RIDGE_ALPHA = 10.0


def _xor_clauses(variables: Sequence[int], rhs: int) -> list[list[int]]:
    return [[-v if bit else v for v, bit in zip(variables, bits)]
            for bits in product((0, 1), repeat=len(variables))
            if sum(bits) % 2 != rhs]


def _shuffle_vars(formula: CNFFormula, rng: Random) -> CNFFormula:
    """Preserve satisfiability with signed variable relabelings and clause order."""
    names = list(range(1, formula.num_vars + 1))
    rng.shuffle(names)
    flips = [rng.choice((-1, 1)) for _ in names]
    clauses = [[(1 if lit > 0 else -1) * names[abs(lit) - 1] * flips[abs(lit) - 1]
                for lit in c] for c in formula.clauses]
    for c in clauses:
        rng.shuffle(c)
    rng.shuffle(clauses)
    return CNFFormula(formula.num_vars, clauses)


def generate_formula(family: str, seed: int) -> CNFFormula:
    """Small, fixed families; seeded; no truth labels enter the generator choice."""
    if family not in FAMILIES:
        raise ValueError(f"unknown generator family: {family}")
    rng = Random(seed + 10_007 * (FAMILIES.index(family) + 1))
    if family in ("random-2SAT", "random-3SAT", "planted-3SAT"):
        n = rng.randint(8, 11)
        k = 2 if family == "random-2SAT" else 3
        ratio = rng.uniform(1.4, 3.4) if k == 2 else rng.uniform(2.8, 5.8)
        m = round(n * ratio)
        planted = rng.randrange(1 << n) if family == "planted-3SAT" else None
        clauses = []
        for _ in range(m):
            variables = rng.sample(range(1, n + 1), k)
            signs = [rng.choice((-1, 1)) for _ in variables]
            clause = [a * v for a, v in zip(signs, variables)]
            if planted is not None and not any(
                    (bool(planted & (1 << (abs(lit) - 1))) == (lit > 0))
                    for lit in clause):
                j = rng.randrange(k)
                clause[j] = -clause[j]
            clauses.append(clause)
        return CNFFormula(n, clauses)
    if family == "random-3XOR":
        n = rng.randint(8, 11)
        q = rng.randint(n - 2, n + 3)
        plant = rng.randrange(1 << n) if rng.randrange(2) else None
        clauses = []
        for _ in range(q):
            variables = sorted(rng.sample(range(1, n + 1), 3))
            rhs = (sum(bool(plant & (1 << (v - 1))) for v in variables) % 2
                   if plant is not None else rng.randrange(2))
            clauses += _xor_clauses(variables, rhs)
        return CNFFormula(n, clauses)
    if family == "tseitin":
        # K4, triangular prism, cube; edge variables, degree-three vertices.
        shape = seed % 3
        if shape == 0:
            edges = list(combinations(range(4), 2))
            vertices = 4
        elif shape == 1:
            edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3),
                     (0, 3), (1, 4), (2, 5)]
            vertices = 6
        else:
            edges = [(i, i ^ (1 << j)) for i in range(8) for j in range(3)
                     if i < (i ^ (1 << j))]
            vertices = 8
        charges = [rng.randrange(2) for _ in range(vertices)]
        charges[-1] = (sum(charges[:-1]) + (seed % 2)) % 2
        clauses = []
        for v in range(vertices):
            incident = [j + 1 for j, (a, b) in enumerate(edges) if a == v or b == v]
            clauses += _xor_clauses(incident, charges[v])
        return _shuffle_vars(CNFFormula(len(edges), clauses), rng)
    # PHP p -> h<p. Repeated relabelings are isomorphic: do not overcount evidence.
    p, h = ((3, 2), (4, 2), (4, 3))[seed % 3]
    var = lambda a, b: a * h + b + 1
    clauses = [[var(a, b) for b in range(h)] for a in range(p)]
    for a, b in combinations(range(p), 2):
        clauses.extend([[-var(a, j), -var(b, j)] for j in range(h)])
    return _shuffle_vars(CNFFormula(p * h, clauses), rng)


def _violation_at(clauses: Sequence[Sequence[int]], assignment: int) -> int:
    mask = 0
    for i, clause in enumerate(clauses):
        if not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause):
            mask |= (1 << i)
    return mask


def sampled_signatures(formula: CNFFormula, *, budget: int, seed: int,
                       max_vars: int = MAX_ENUM_VARS) -> tuple[int, ...]:
    """Sample unique assignments, strictly less than the total state space."""
    _check_formula(formula, max_vars)
    if not isinstance(budget, int) or budget < 1 or budget >= (1 << formula.num_vars):
        raise ValueError("sample budget must be positive and strictly below 2^n")
    indices = Random(seed).sample(range(1 << formula.num_vars), budget)
    return tuple(_violation_at(formula.clauses, x) for x in indices)


def _split_sampled_signatures(formula: CNFFormula, budget: int,
                              seed: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    _check_formula(formula, MAX_ENUM_VARS)
    if not isinstance(budget, int) or budget < 2 or budget >= (1 << formula.num_vars):
        raise ValueError("sample total must fit strictly below 2^n")
    indices = Random(seed).sample(range(1 << formula.num_vars), budget)
    half = budget // 2
    return (tuple(_violation_at(formula.clauses, x) for x in indices[:half]),
            tuple(_violation_at(formula.clauses, x) for x in indices[half:]))


def _xor_pattern_fraction(formula: CNFFormula) -> float:
    """Conventional literal sign-pattern detector, not an XOR SAT solver."""
    buckets: dict[tuple[int, ...], set[int]] = {}
    for clause in formula.clauses:
        vv = [abs(lit) for lit in clause]
        if len(vv) not in (2, 3) or len(set(vv)) != len(vv):
            continue
        variables = tuple(sorted(vv))
        sign_by_var = {abs(lit): lit < 0 for lit in clause}
        mask = sum(1 << j for j, v in enumerate(variables) if sign_by_var[v])
        buckets.setdefault(variables, set()).add(mask)
    accounted = 0
    for vv, masks in buckets.items():
        if len(masks) == (1 << (len(vv) - 1)):
            if len({m.bit_count() % 2 for m in masks}) == 1:
                accounted += len(masks)
    return accounted / max(1, len(formula.clauses))


def structural_features(formula: CNFFormula) -> tuple[float, ...]:
    _check_formula(formula, MAX_ENUM_VARS)
    n = formula.num_vars
    if n == 0:
        raise ValueError("cross-instance probe needs at least one variable")
    m = len(formula.clauses)
    widths = [len(c) for c in formula.clauses]
    pos, neg = [0] * n, [0] * n
    for clause in formula.clauses:
        for literal in clause:
            (pos if literal > 0 else neg)[abs(literal) - 1] += 1
    degrees = [p + q for p, q in zip(pos, neg)]
    mean_deg = sum(degrees) / n
    sd_deg = sqrt(sum((d - mean_deg) ** 2 for d in degrees) / n)
    return (float(n), m / n, sum(widths) / max(m, 1),
            sum(w == 2 for w in widths) / max(m, 1),
            sum(w == 1 for w in widths) / max(m, 1),
            max(degrees, default=0) / n,
            sd_deg / max(mean_deg, 1.0),
            sum(abs(p - q) for p, q in zip(pos, neg)) / max(sum(degrees), 1),
            _xor_pattern_fraction(formula))


def _aggregate_violation_features(train: Sequence[int], probe: Sequence[int],
                                  m: int) -> tuple[float, ...]:
    masks = tuple(train) + tuple(probe)
    values = [v.bit_count() / max(m, 1) for v in masks]
    mean = sum(values) / len(values)
    dev = sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    return (mean, dev, sum(v == 0 for v in masks) / len(masks),
            len(set(masks)) / len(masks))


def _geometry_features(probe: Sequence[int], rows: Sequence[int], m: int) -> tuple[float, ...]:
    inc = incidence_overlap(probe, rows, m)
    num_nonmodel = sum(v != 0 for v in probe)
    survived = sum(v != 0 and all(parity_accepts(v, row) for row in rows)
                   for v in probe)
    return ((num_nonmodel - survived) / max(num_nonmodel, 1),
            inc.top_gram_eigenvalue / max(inc.active_rows, 1),
            inc.mean_pairwise_cosine,
            inc.maximum_multiplicity / max(inc.active_rows, 1))


def _dpll_search_nodes(formula: CNFFormula) -> int:
    """Deterministic unit-propagating DPLL reference effort, NOT CDCL time."""
    clauses = formula.clauses
    calls = 0

    def dfs(assign: dict[int, bool]) -> bool:
        nonlocal calls
        calls += 1
        values = assign.copy()
        while True:
            changed = False
            all_satisfied = True
            for clause in clauses:
                unassigned = []
                satisfied = False
                for literal in clause:
                    var = abs(literal)
                    if var in values:
                        if values[var] == (literal > 0):
                            satisfied = True
                            break
                    else:
                        unassigned.append(literal)
                if satisfied:
                    continue
                all_satisfied = False
                if not unassigned:
                    return False
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    var = abs(lit)
                    implied = lit > 0
                    if var in values and values[var] != implied:
                        return False
                    if var not in values:
                        values[var] = implied
                        changed = True
            if all_satisfied:
                return True
            if not changed:
                break
        var = next((v for v in range(1, formula.num_vars + 1) if v not in values), None)
        if var is None:
            return False
        for bit in (False, True):
            extended = values.copy()
            extended[var] = bit
            if dfs(extended):
                return True
        return False

    dfs({})
    return calls


@dataclass(frozen=True)
class FormulaRecord:
    family: str
    seed: int
    n: int
    m: int
    dpll_nodes: int
    target_log2_nodes: float
    features: tuple[float, ...]
    structural_ns: int
    sampling_ns: int
    row_selection_ns: int
    geometry_ns: int
    null_geometry_ns: int
    centered_ns: int
    null_centered_ns: int
    dpll_ns: int

    @property
    def measured_feature_ns(self) -> int:
        return (self.structural_ns + self.sampling_ns +
                self.row_selection_ns + self.geometry_ns + self.centered_ns)


def record_formula(formula: CNFFormula, family: str, seed: int, *,
                   budget: int = 48, rows: int = 6, candidate_budget: int = 96,
                   seed_offset: int = 0) -> FormulaRecord:
    """Compute pre-solving predictors and separate held-out effort target."""
    if rows < 0 or rows > 32:
        raise ValueError("rows outside [0,32]")
    if not 2 <= budget < (1 << formula.num_vars):
        raise ValueError("sample budget exhausted assignment space")
    m = len(formula.clauses)
    if candidate_budget < m:
        raise ValueError("candidate budget below number of clauses")
    ts = perf_counter_ns()
    s = structural_features(formula)
    struct_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    train, probe = _split_sampled_signatures(formula, budget, seed + seed_offset * 100003 + 1081)
    sampled = _aggregate_violation_features(train, probe, m)
    sampling_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    learned_rows = greedy_violation_rows(train, m, max_rows=rows,
                                        max_weight=3, candidate_budget=candidate_budget,
                                        candidate_seed=seed + seed_offset * 37 + 1057)
    selection_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    learned = _geometry_features(probe, learned_rows, m)
    geom_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    null_rows = matched_random_rows(learned_rows, m, seed + seed_offset * 73 + 23)
    null = _geometry_features(probe, null_rows, m)
    null_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    center = centered_incidence(probe, learned_rows, m)
    center_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    center_null = centered_incidence(probe, null_rows, m)
    center_null_ns = perf_counter_ns() - ts
    ts = perf_counter_ns()
    dpll_nodes = _dpll_search_nodes(formula)
    dpll_ns = perf_counter_ns() - ts
    return FormulaRecord(
        family, seed, formula.num_vars, m, dpll_nodes,
        log2(1 + dpll_nodes),
        s + sampled + learned + null +
        (center.largest_eigenvalue_per_check,
         center.mean_absolute_correlation,
         center.signed_triangle_frustration, center.triangle_mass) +
        (center_null.largest_eigenvalue_per_check,
         center_null.mean_absolute_correlation,
         center_null.signed_triangle_frustration, center_null.triangle_mass),
        struct_ns, sampling_ns, selection_ns, geom_ns, null_ns,
        center_ns, center_null_ns, dpll_ns)


FEATURE_INDEX = {name: i for i, name in enumerate(STRUCTURAL + SAMPLED + LEARNED + NULL + CENTERED + CENTERED_NULL)}
PREDICTORS = {
    "constant": (),
    "structure": STRUCTURAL,
    "structure+sample": STRUCTURAL + SAMPLED,
    "structure+sample+null": STRUCTURAL + SAMPLED + NULL,
    "structure+sample+learned-pass": STRUCTURAL + SAMPLED + LEARNED[:1],
    "structure+sample+learned-gram": STRUCTURAL + SAMPLED + LEARNED,
    "structure+sample+centered": STRUCTURAL + SAMPLED + CENTERED,
    "structure+sample+null-centered": STRUCTURAL + SAMPLED + CENTERED_NULL,
    "structure+sample+all-geometry": STRUCTURAL + SAMPLED + LEARNED + CENTERED,
}


def _predict_ridge(train: Sequence[FormulaRecord],
                   test: Sequence[FormulaRecord], names: Sequence[str],
                   alpha: float = RIDGE_ALPHA) -> np.ndarray:
    y = np.array([v.target_log2_nodes for v in train], dtype=float)
    if not names:
        return np.full(len(test), y.mean())
    indices = [FEATURE_INDEX[name] for name in names]
    X = np.array([[v.features[i] for i in indices] for v in train], dtype=float)
    Z = np.array([[v.features[i] for i in indices] for v in test], dtype=float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd < 1e-12] = 1.0
    X = (X - mu) / sd
    Z = (Z - mu) / sd
    design = np.column_stack((np.ones(len(X)), X))
    penalty = np.diag([0.0] + [float(alpha)] * X.shape[1])
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    return np.column_stack((np.ones(len(Z)), Z)) @ coefficients


@dataclass(frozen=True)
class FoldResult:
    heldout_family: str
    instances: int
    min_nodes: int
    median_nodes: float
    max_nodes: int
    mae_log2_by_predictor: dict[str, float]


@dataclass(frozen=True)
class CrossInstanceReport:
    seed_count: int
    instances: int
    sample_budget: int
    row_budget: int
    candidate_budget: int
    folds: tuple[FoldResult, ...]
    overall_mae_log2: dict[str, float]
    median_feature_ms: float
    median_structural_ms: float
    median_null_ms: float
    median_dpll_ms: float
    median_centered_ms: float
    max_enum_vars: int
    evidence_level: str = "M: finite measured DPLL-reference effort only"


def cross_instance_benchmark(*, seed_count: int = 12, sample_budget: int = 48,
                             rows: int = 6, candidate_budget: int = 96,
                             seed_offset: int = 0) -> CrossInstanceReport:
    """Leave one generator FAMILY out per fold; report every fold and null."""
    if not 2 <= seed_count <= 32:
        raise ValueError("seed_count must be in [2,32]")
    dataset = []
    for family in FAMILIES:
        for seed in range(seed_count):
            formula = generate_formula(family, seed)
            dataset.append(record_formula(formula, family, seed,
                           budget=sample_budget, rows=rows,
                           candidate_budget=candidate_budget,
                           seed_offset=seed_offset))
    folds = []
    accum = {name: 0.0 for name in PREDICTORS}
    for heldout in FAMILIES:
        train = [r for r in dataset if r.family != heldout]
        test = [r for r in dataset if r.family == heldout]
        actual = np.array([r.target_log2_nodes for r in test])
        losses = {}
        for name, features in PREDICTORS.items():
            predicted = _predict_ridge(train, test, features)
            losses[name] = float(np.mean(np.abs(predicted - actual)))
            accum[name] += losses[name] * len(test)
        nodes = sorted(v.dpll_nodes for v in test)
        folds.append(FoldResult(heldout, len(test), nodes[0],
                                (nodes[(len(nodes)-1)//2] + nodes[len(nodes)//2]) / 2,
                                nodes[-1], losses))
    full = {name: error / len(dataset) for name, error in accum.items()}
    return CrossInstanceReport(
        seed_count, len(dataset), sample_budget, rows, candidate_budget,
        tuple(folds), full,
        float(np.median([r.measured_feature_ns / 1e6 for r in dataset])),
        float(np.median([r.structural_ns / 1e6 for r in dataset])),
        float(np.median([r.null_geometry_ns / 1e6 for r in dataset])),
        float(np.median([r.dpll_ns / 1e6 for r in dataset])),
        float(np.median([r.centered_ns / 1e6 for r in dataset])),
        MAX_ENUM_VARS)
