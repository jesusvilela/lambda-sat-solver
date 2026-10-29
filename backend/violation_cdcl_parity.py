"""Formula-only GF(2) positive control for the external CDCL topology study.

Runs the existing λSAT XOR extractor and frame without modifying its
certification path. This addendum was planned *after* seeing the first
36-formula CDCL pilot: exploratory, not retroactive preregistration.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import median
from time import perf_counter_ns

import numpy as np

from .cnf_utils import CNFFormula
from .xor_extraction import extract_xors, _rref_gf2, gf2_xor_solve
from .violation_cdcl_topology import (
    BASE, SIGN, NULL, FAMILIES, RIDGE_ALPHA,
    TopologyRecord, generate_formula, topology_benchmark,
)

GF2 = ("recovered_xor_fraction", "xor_constraint_density",
       "xor_rank_per_variable", "xor_rank_deficiency",
       "xor_inconsistent")
ALL_FEATURES = BASE + SIGN + NULL + GF2
COLUMNS = {name: i for i,name in enumerate(ALL_FEATURES)}
PREDICTORS = {
    "classical": BASE,
    "classical+signed": BASE + SIGN,
    "classical+topology-null": BASE + NULL,
    "classical+GF2": BASE + GF2,
    "classical+GF2+signed": BASE + GF2 + SIGN,
    "classical+GF2+topology-null": BASE + GF2 + NULL,
    "GF2-only": GF2,
}


@dataclass(frozen=True)
class GF2Control:
    features: tuple[float,...]
    frame_status: str
    extracted_constraints: int
    rank: int
    elapsed_ms: float


def gf2_control(formula: CNFFormula) -> GF2Control:
    """Time actual algebraic extraction/solve; no CDCL calls or labels."""
    start=perf_counter_ns()
    parsed=extract_xors(formula)
    n=formula.num_vars
    augmented=[]
    spanned=set()
    for xor in parsed.xors:
        row=0
        for var in xor.variables:
            if not 1<=var<=n:
                raise AssertionError("malformed extracted XOR")
            row|=1<<(var-1)
            spanned.add(var)
        if xor.rhs:
            row|=1<<n
        augmented.append(row)
    original=_rref_gf2(augmented,n)
    variable_basis=_rref_gf2([v & ((1<<n)-1) for v in augmented],n)
    if variable_basis is None:
        raise AssertionError("homogeneous coefficient matrix cannot be inconsistent")
    rank=len(variable_basis)
    inconsistent=original is None
    state=gf2_xor_solve(formula)
    if (state.status=="UNSAT")!=inconsistent:
        raise AssertionError("internal GF2 frame/linear-consistency mismatch")
    if state.status=="SAT" and state.model is None:
        raise AssertionError("GF2 SAT frame must supply a model")
    elapsed=(perf_counter_ns()-start)/1e6
    return GF2Control((
        parsed.xor_clause_fraction,
        len(parsed.xors)/max(len(formula.clauses),1),
        rank/max(n,1),
        (len(spanned)-rank)/max(len(spanned),1),
        float(inconsistent),
    ),state.status,len(parsed.xors),rank,elapsed)


@dataclass(frozen=True)
class AugmentedRecord:
    base: TopologyRecord
    gf2: GF2Control

    @property
    def features(self):
        return self.base.features+self.gf2.features

    @property
    def capped_log_conflicts(self):
        return self.base.capped_log_conflicts


def _predict(train: list[AugmentedRecord],test: list[AugmentedRecord],
             names: tuple[str,...]) -> np.ndarray:
    target=np.asarray([r.capped_log_conflicts for r in train],dtype=float)
    if not names:
        return np.full(len(test),float(target.mean()))
    ix=[COLUMNS[s] for s in names]
    X=np.asarray([[r.features[i] for i in ix] for r in train],dtype=float)
    Z=np.asarray([[r.features[i] for i in ix] for r in test],dtype=float)
    mean,std=X.mean(axis=0),X.std(axis=0)
    std[std<1e-12]=1.
    X,Z=(X-mean)/std,(Z-mean)/std
    X=np.column_stack((np.ones(len(X)),X))
    Z=np.column_stack((np.ones(len(Z)),Z))
    penalty=np.diag([0.]+[RIDGE_ALPHA]*len(ix))
    return Z@np.linalg.solve(X.T@X+penalty,X.T@target)


def _loss(train: list[AugmentedRecord],
          test: list[AugmentedRecord]) -> dict[str,float]:
    truth=np.asarray([r.capped_log_conflicts for r in test])
    return {name:float(np.mean(np.abs(_predict(train,test,columns)-truth)))
            for name,columns in PREDICTORS.items()}


@dataclass(frozen=True)
class GF2Fold:
    heldout: str
    count: int
    mae_log2_capped_conflicts: dict[str,float]


@dataclass(frozen=True)
class GF2Report:
    formulas: int
    seed_start: int
    seed_count: int
    sizes: tuple[int,...]
    status_counts: dict[str,int]
    pure_xor_checked: int
    family_holdouts: tuple[GF2Fold,...]
    largest_size_holdout: GF2Fold | None
    aggregate_mae: dict[str,float]
    median_gf2_ms: float
    median_cdcl_ms: float
    censored_call_fraction: float
    match_error_count: int
    provenance: str="post-pilot exploratory control; existing sound λSAT GF2 gate"


def parity_holdout(*,seeds: int=6,seed_start: int=100,
                   sizes: tuple[int,...]=(48,72,96),
                   orbits: int=3,budget: int=5000,swaps: int=160
                   ) -> GF2Report:
    """Independent seed range, same CDCL calls, existing XOR frame comparison."""
    original=topology_benchmark(seeds=seeds,seed_start=seed_start,
         sizes=sizes,orbits=orbits,budget=budget,swaps=swaps)
    dataset=[]
    for rec in original.records:
        f=generate_formula(rec.family,rec.size,rec.seed)
        ctrl=gf2_control(f)
        # A resolved CDCL result must not disagree with a sound GF(2) gate.
        for call in rec.calls:
            if (ctrl.frame_status!="INCONCLUSIVE" and call.status!="UNKNOWN"
                    and call.status!=ctrl.frame_status):
                raise AssertionError("CDCL result contradicts independent GF(2) frame")
        dataset.append(AugmentedRecord(rec,ctrl))
    groups=[]
    totals={name:0. for name in PREDICTORS}
    for heldout in FAMILIES:
        train=[r for r in dataset if r.base.family!=heldout]
        test=[r for r in dataset if r.base.family==heldout]
        errors=_loss(train,test)
        groups.append(GF2Fold(heldout,len(test),errors))
        for name,value in errors.items():
            totals[name]+=len(test)*value
    largest=max(sizes)
    test=[r for r in dataset if r.base.size==largest]
    train=[r for r in dataset if r.base.size!=largest]
    sizefold=GF2Fold("n="+str(largest),len(test),_loss(train,test)) if train else None
    counts={name:sum(r.gf2.frame_status==name for r in dataset)
            for name in ("SAT","UNSAT","INCONCLUSIVE")}
    pure=sum(r.gf2.frame_status in ("SAT","UNSAT") for r in dataset)
    return GF2Report(len(dataset),seed_start,seeds,tuple(sizes),
        counts,pure,tuple(groups),sizefold,
        {name:value/len(dataset) for name,value in totals.items()},
        median(r.gf2.elapsed_ms for r in dataset),
        original.median_cdcl_ms,original.censored_call_fraction,0)
