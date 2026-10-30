"""Hold-out family probe with relabeling-robust DPLL effort and signed incidence.

The signed connection is computed BEFORE any DPLL calls. DPLL nodes are
research outcomes, never SAT verdicts or proof certificates. The checkerboard
null preserves support plus both clause and variable sign margins; it does
NOT preserve satisfiability in general, so it is ONLY a feature null.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log2
from random import Random
from statistics import mean, median
from time import perf_counter_ns

import numpy as np

from .cnf_utils import CNFFormula
from .violation_connection import (signed_connection, connection_features,
                                   margin_matched_sign_null)
from .violation_cross_instance import (FAMILIES, STRUCTURAL,
    generate_formula, structural_features, _dpll_search_nodes, _shuffle_vars)

SIGNED = ('cycle_rank_per_edge', 'negative_cycle_obstruction',
          'negative_square_fraction', 'square_density', 'squares_per_edge')
NULL = tuple('null_' + x for x in SIGNED)
FEATURES = STRUCTURAL + SIGNED + NULL
INDICES = {name: i for i, name in enumerate(FEATURES)}
PREDICTORS = {
    'constant': (),
    'structure': STRUCTURAL,
    'structure+signed-connection': STRUCTURAL + SIGNED,
    'structure+margin-null': STRUCTURAL + NULL,
    'signed-only': SIGNED,
}


@dataclass(frozen=True)
class OrbitSample:
    family: str
    seed: int
    features: tuple[float, ...]
    raw_log_nodes: float
    orbit_median_log_nodes: float
    orbit_log_node_range: float
    distinct_orbit_counts: int
    successful_null_switches: int
    structural_ns: int
    signed_ns: int
    null_ns: int
    reference_ns: int


def orbit_effort(formula: CNFFormula, *, seed: int,
                 repeats: int = 8) -> tuple[float, float, int, float]:
    """Median log2(1+search nodes) over reproducible signed relabelings.

    Finite Monte Carlo averaging is NOT exactly gauge invariant; its purpose
    is to reduce lexicographic branch/phase artifacts in the measured target.
    """
    if not 2 <= repeats <= 24:
        raise ValueError('orbit repeats must be 2..24')
    nodes = [_dpll_search_nodes(_shuffle_vars(formula, Random(
             seed * 1000003 + 2009 * i + 17011))) for i in range(repeats)]
    logs = [log2(1+x) for x in nodes]
    return median(logs), max(logs)-min(logs), len(set(nodes)), mean(nodes)


def measure_orbit_record(formula: CNFFormula, family: str, seed: int, *,
                         repeats: int = 8, null_swaps: int = 32,
                         offset: int = 0) -> OrbitSample:
    if family not in FAMILIES:
        raise ValueError('unknown family')
    start = perf_counter_ns()
    base = structural_features(formula)
    structural_ns = perf_counter_ns() - start
    start = perf_counter_ns()
    sign = connection_features(signed_connection(formula))
    signed_ns = perf_counter_ns() - start
    start = perf_counter_ns()
    null_formula, successful = margin_matched_sign_null(
        formula, seed=seed + 331*offset + 173, target_swaps=null_swaps)
    null_sign = connection_features(signed_connection(null_formula))
    null_ns = perf_counter_ns() - start
    start = perf_counter_ns()
    raw_nodes = _dpll_search_nodes(formula)
    robust, spread, distinct, _ = orbit_effort(
        formula, seed=seed + 10007 * (FAMILIES.index(family)+1) + offset*313,
        repeats=repeats)
    reference_ns = perf_counter_ns() - start
    return OrbitSample(family,seed,base+sign+null_sign,log2(1+raw_nodes),
                       robust,spread,distinct,successful,
                       structural_ns,signed_ns,null_ns,reference_ns)


def _ridge_predict(train, test, columns, outcome):
    y = np.array([getattr(v, outcome) for v in train], dtype=float)
    if not columns:
        return np.full(len(test), float(y.mean()))
    positions = [INDICES[name] for name in columns]
    a = np.array([[v.features[i] for i in positions] for v in train])
    b = np.array([[v.features[i] for i in positions] for v in test])
    mu,sd = a.mean(axis=0),a.std(axis=0)
    sd[sd<1e-12] = 1.0
    a,b=(a-mu)/sd,(b-mu)/sd
    a=np.column_stack((np.ones(len(a)),a))
    b=np.column_stack((np.ones(len(b)),b))
    penalty=np.diag([0.0]+[10.0]*len(positions))
    return b @ np.linalg.solve(a.T @ a + penalty,a.T @ y)


@dataclass(frozen=True)
class OrbitFold:
    heldout_family: str
    size: int
    raw_mae: dict[str,float]
    orbit_mae: dict[str,float]
    median_orbit_spread: float
    fraction_orbits_varying: float
    null_switches_success: int


@dataclass(frozen=True)
class OrbitReport:
    formulas: int
    seed_count: int
    orbit_repeats: int
    folds: tuple[OrbitFold,...]
    overall_raw_mae: dict[str,float]
    overall_orbit_mae: dict[str,float]
    median_feature_ms: float
    median_structure_ms: float
    median_reference_ms: float
    fraction_nulls_with_switches: float
    median_orbit_range: float
    evidence: str = 'M: finite relabeling-averaged reference DPLL, no solver speed claim'


def orbit_holdout_benchmark(*,seed_count: int = 12, repeats: int = 8,
                            null_swaps: int = 32, offset: int = 0) -> OrbitReport:
    if not 2 <= seed_count <= 32 or not 0 <= offset <= 100000:
        raise ValueError('seed or offset budget exceeded')
    dataset = [measure_orbit_record(generate_formula(fam,seed),fam,seed,
                    repeats=repeats,null_swaps=null_swaps,offset=offset)
               for fam in FAMILIES for seed in range(seed_count)]
    folds=[]
    raw,orbit=({name:0.0 for name in PREDICTORS} for _ in range(2))
    for heldout in FAMILIES:
        train=[v for v in dataset if v.family!=heldout]
        test=[v for v in dataset if v.family==heldout]
        by_target=[]
        for target,acc in [('raw_log_nodes',raw),('orbit_median_log_nodes',orbit)]:
            true=np.array([getattr(v,target) for v in test])
            loss={}
            for name,cols in PREDICTORS.items():
                guess=_ridge_predict(train,test,cols,target)
                loss[name]=float(np.mean(abs(guess-true)))
                acc[name]+=len(test)*loss[name]
            by_target.append(loss)
        folds.append(OrbitFold(heldout,len(test),by_target[0],by_target[1],
            median(v.orbit_log_node_range for v in test),
            sum(v.distinct_orbit_counts>1 for v in test)/len(test),
            sum(v.successful_null_switches>0 for v in test)))
    return OrbitReport(len(dataset),seed_count,repeats,tuple(folds),
        {key:value/len(dataset) for key,value in raw.items()},
        {key:value/len(dataset) for key,value in orbit.items()},
        median((v.structural_ns+v.signed_ns)/1e6 for v in dataset),
        median(v.structural_ns/1e6 for v in dataset),
        median(v.reference_ns/1e6 for v in dataset),
        sum(v.successful_null_switches>0 for v in dataset)/len(dataset),
        median(v.orbit_log_node_range for v in dataset))
