"""Held-out topology benchmark: finite signed graph features vs external CDCL effort.

Fully independent of λSAT production routing and certification. PySAT Glucose4
is an experimental CDCL oracle, not part of the trusted base. A conflict cap
produces censored UNKNOWN outcomes; all prediction targets are explicitly
budget-capped. No Kakeya, smoothing, NP-hardness or asymptotic claim follows.

The source contract is docs/ladder/VIOLATION_CDCL_TOPOLOGY_PREREG.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations, product
from math import log2, sqrt
from random import Random
from statistics import median
from time import perf_counter_ns
from typing import Callable, Sequence

import numpy as np

from .cnf_utils import CNFFormula
from .violation_connection import signed_connection
from .violation_cross_instance import _shuffle_vars, _xor_clauses

FAMILIES = ("uniform3", "ring3", "community3", "hub3",
            "tseitin-prism", "tseitin-rewired")
BASE = ("n", "clauses_per_variable", "mean_width", "binary_fraction",
        "unit_fraction", "maximum_occurrence_per_variable", "degree_cv",
        "literal_polarity_imbalance", "xor_pattern_fraction",
        "components_per_variable", "unsigned_cycle_rank_per_edge",
        "unsigned_squares_per_edge", "unsigned_square_density")
SIGN = ("negative_square_fraction", "negative_squares_per_edge",
        "fraction_unbalanced_components", "unbalanced_any")
NULL = tuple("rewired_" + name for name in SIGN)
FEATURES = BASE + SIGN + NULL
COLS = {name: i for i, name in enumerate(FEATURES)}
PREDICTORS = {
    "constant": (),
    "classical": BASE,
    "classical+signed": BASE + SIGN,
    "classical+rewired-null": BASE + NULL,
    "signed-only": SIGN,
}
RIDGE_ALPHA = 10.0


def _connected(edges: set[tuple[int, int]], vertices: int) -> bool:
    adj = [[] for _ in range(vertices)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen, stack = {0}, [0]
    while stack:
        for v in adj[stack.pop()]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == vertices


def cubic_graph(vertices: int, topology: str, seed: int) -> tuple[tuple[int, int], ...]:
    """Connected, simple cubic prism, optionally degree-preserving rewired.

    The random-rewired family starts from a prism but its edge switches change
    graph topology, not just variable labels or clause signs.
    """
    if vertices < 8 or vertices % 2 or topology not in ("prism", "rewired"):
        raise ValueError("cubic graph needs an even vertex count >=8 and a known topology")
    half = vertices // 2
    edges: set[tuple[int, int]] = set()
    def edge(a: int, b: int) -> tuple[int, int]:
        return (min(a, b), max(a, b))
    for i in range(half):
        edges.add(edge(i, (i + 1) % half))
        edges.add(edge(half + i, half + (i + 1) % half))
        edges.add(edge(i, half + i))
    if topology == "rewired":
        rng = Random(seed + 90101)
        accepted = 0
        for _ in range(vertices * 400):
            if accepted >= vertices * 8:
                break
            first, second = rng.sample(sorted(edges), 2)
            a, b = first
            c, d = second
            if len({a, b, c, d}) != 4:
                continue
            if rng.randrange(2):
                new = {edge(a, c), edge(b, d)}
            else:
                new = {edge(a, d), edge(b, c)}
            if len(new) < 2 or any(e in edges for e in new):
                continue
            trial = (edges - {first, second}) | new
            if not _connected(trial, vertices):
                continue
            edges = trial
            accepted += 1
        if accepted < vertices:
            raise RuntimeError("cubic rewiring failed its nontriviality budget")
    degree = [0] * vertices
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    if len(edges) != 3 * vertices // 2 or any(d != 3 for d in degree) or not _connected(edges, vertices):
        raise AssertionError("cubic graph contract violated")
    return tuple(sorted(edges))


def _weighted_sample3(rng: Random, n: int) -> list[int]:
    weights = [1.0 / (v + 3) ** 0.7 for v in range(n)]
    available = list(range(1, n + 1))
    output = []
    for _ in range(3):
        k = rng.choices(range(len(available)),
                        weights=[weights[v - 1] for v in available], k=1)[0]
        output.append(available.pop(k))
    return output


def generate_formula(family: str, size: int, seed: int) -> CNFFormula:
    """Distinct seeded graphs at n=48/72/96 and small n=12 for theorem tests.

    Tseitin formulas have variable count 3*vertices/2 == size; clause count
    4*vertices. Their signed charges are consistent iff seed is even.
    """
    if family not in FAMILIES or size < 12 or size % 3:
        raise ValueError("unknown family or invalid variable size")
    rng = Random(seed * 10007 + size * 421 + FAMILIES.index(family) * 1000003)
    if family.startswith("tseitin-"):
        vertices = 2 * size // 3
        edges = cubic_graph(vertices, "prism" if family.endswith("prism") else "rewired", seed)
        charges = [rng.randrange(2) for _ in range(vertices)]
        charges[-1] = (sum(charges[:-1]) + seed % 2) % 2
        clauses: list[list[int]] = []
        for vertex in range(vertices):
            inc = [i+1 for i,(a,b) in enumerate(edges) if a == vertex or b == vertex]
            if len(inc) != 3:
                raise AssertionError("invalid cubic incidence")
            clauses.extend(_xor_clauses(inc, charges[vertex]))
        return CNFFormula(size, clauses)

    n = size
    m = round(4.26 * n)
    clauses = []
    seen = set()
    radius = max(4, n // 12)
    block_size = n // 4
    attempts = 0
    while len(clauses) < m:
        attempts += 1
        if attempts > 200 * m:
            raise RuntimeError("cannot generate enough distinct signed clauses")
        if family == "uniform3":
            variables = rng.sample(range(1,n+1), 3)
        elif family == "ring3":
            if rng.random() < 0.20:
                variables = rng.sample(range(1,n+1), 3)
            else:
                center = rng.randrange(n)
                pool = [((center + offset) % n) + 1
                        for offset in range(-radius, radius+1)]
                variables = rng.sample(pool, 3)
        elif family == "community3":
            if rng.random() < 0.15:
                variables = rng.sample(range(1,n+1), 3)
            else:
                block = rng.randrange(4)
                start = block * block_size
                stop = n if block == 3 else start + block_size
                variables = rng.sample(range(start+1, stop+1), 3)
        else:
            variables = _weighted_sample3(rng,n)
        clause = [v*rng.choice((-1,1)) for v in variables]
        key = tuple(sorted(clause))
        if key not in seen:
            seen.add(key)
            clauses.append(clause)
    return CNFFormula(n,clauses)


def support_degree_sign_null(formula: CNFFormula, *, seed: int,
                             swaps: int = 160) -> tuple[CNFFormula,int]:
    """Rewire two same-sign literal incidences; preserve exact sign margins.

    Keeps n, m, every clause width and +/- count, variable total degrees
    and variable positive/negative occurrence counts. Unlike relabeling, it
    can change SAT, signed topology and conflict work. Feature-null only.
    """
    if not 0 <= swaps <= 2048:
        raise ValueError("invalid swap budget")
    clauses = [list(c) for c in formula.clauses]
    if any(len({abs(l) for l in c}) != len(c) for c in clauses):
        raise ValueError("null needs non-tautological simple clauses")
    rng = Random(seed)
    done = 0
    for _ in range(swaps*30):
        if done >= swaps or len(clauses) < 2:
            break
        a,b = rng.sample(range(len(clauses)), 2)
        if not clauses[a] or not clauses[b]:
            continue
        i,j = rng.randrange(len(clauses[a])),rng.randrange(len(clauses[b]))
        la,lb = clauses[a][i],clauses[b][j]
        if ((la > 0) != (lb > 0) or abs(la) == abs(lb) or
            abs(la) in [abs(v) for v in clauses[b]] or
            abs(lb) in [abs(v) for v in clauses[a]]):
            continue
        clauses[a][i], clauses[b][j] = lb,la
        done += 1
    return CNFFormula(formula.num_vars,clauses),done


def _xor_pattern_fraction(formula: CNFFormula) -> float:
    groups: dict[tuple[int,...],set[int]] = {}
    for clause in formula.clauses:
        vv = [abs(lit) for lit in clause]
        if len(vv) not in (2,3) or len(set(vv)) != len(vv):
            continue
        vs = tuple(sorted(vv))
        signs = {abs(lit):lit<0 for lit in clause}
        mask = sum(1<<k for k,v in enumerate(vs) if signs[v])
        groups.setdefault(vs,set()).add(mask)
    count = sum(len(patterns) for vs,patterns in groups.items()
                if len(patterns)==(1<<(len(vs)-1)) and
                len({p.bit_count()%2 for p in patterns})==1)
    return count / max(1,len(formula.clauses))


def _structural(formula: CNFFormula) -> tuple[float,...]:
    n,m = formula.num_vars,len(formula.clauses)
    if n < 1:
        raise ValueError("zero declared variables")
    widths = [len(c) for c in formula.clauses]
    pos,neg=[0]*n,[0]*n
    for c in formula.clauses:
        for lit in c:
            if not 1<=abs(lit)<=n:
                raise ValueError("literal outside declared variables")
            (pos if lit>0 else neg)[abs(lit)-1] += 1
    deg = [a+b for a,b in zip(pos,neg)]
    avg = sum(deg)/n
    cv = sqrt(sum((x-avg)**2 for x in deg)/n)/max(avg,1.)
    return (float(n),m/n,
            sum(widths)/max(m,1),sum(w==2 for w in widths)/max(m,1),
            sum(w==1 for w in widths)/max(m,1),
            max(deg,default=0)/n,cv,
            sum(abs(a-b) for a,b in zip(pos,neg))/max(sum(deg),1),
            _xor_pattern_fraction(formula))


def _signed_features(sig) -> tuple[float,...]:
    return (sig.negative_square_fraction,
            sig.negative_four_cycles/max(sig.edges,1),
            (sig.components-sig.balanced_components)/max(sig.components,1),
            float(not sig.globally_balanced))


def extract_features(formula: CNFFormula, *, null_seed: int, swaps: int = 160
                     ) -> tuple[tuple[float,...],int,int,int]:
    """Return (features, baseline_ns, extra_signed_ns, null_ns). No solver calls."""
    start=perf_counter_ns()
    struct = _structural(formula)
    sig = signed_connection(formula,max_wedges=500000)
    baseline = struct + (sig.components/max(formula.num_vars,1),
        sig.cycle_rank/max(sig.edges,1),
        sig.four_cycles/max(sig.edges,1),sig.square_density)
    baseline_ns=perf_counter_ns()-start
    start=perf_counter_ns()
    signed = _signed_features(sig)
    signed_ns=perf_counter_ns()-start
    start=perf_counter_ns()
    rewired,count=support_degree_sign_null(formula,seed=null_seed,swaps=swaps)
    null_signed=_signed_features(signed_connection(rewired,max_wedges=500000))
    null_ns=perf_counter_ns()-start
    if len(baseline+signed+null_signed)!=len(FEATURES):
        raise AssertionError("feature contract")
    return baseline+signed+null_signed,count,baseline_ns,signed_ns+null_ns


def canonical_labeled_digest(formula: CNFFormula) -> str:
    """Labels are kept. This detects duplicate CNFs, not graph isomorphism."""
    data = repr((formula.num_vars,sorted(tuple(sorted(c)) for c in formula.clauses)))
    return sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CDCLCall:
    status: str
    conflicts: int
    decisions: int
    propagations: int
    wall_ms: float
    valid_sat_model: bool | None


def _model_replay(formula: CNFFormula, model: Sequence[int] | None) -> bool:
    if model is None:
        return False
    values = {abs(v):v>0 for v in model if 0<abs(v)<=formula.num_vars}
    return all(any(values.get(abs(lit))==(lit>0) for lit in clause)
               for clause in formula.clauses)


def cdcl_call(formula: CNFFormula, *, budget: int = 2000, engine: str="g4",
              solver_factory: Callable | None = None) -> CDCLCall:
    """External CDCL observation with a conflict cap, model replay and no TCB change."""
    if not 1 <= budget <= 100000:
        raise ValueError("conflict budget out of bounds")
    if solver_factory is None:
        try:
            from pysat.solvers import Solver
        except ImportError as exc:
            raise RuntimeError("external CDCL experiment requires pip install python-sat") from exc
        solver_factory=Solver
    start=perf_counter_ns()
    with solver_factory(name=engine,bootstrap_with=formula.clauses,use_timer=False) as solver:
        solver.conf_budget(budget)
        answer=solver.solve_limited()
        stats=solver.accum_stats()
        valid=None
        if answer is True:
            valid=_model_replay(formula,solver.get_model())
            if not valid:
                raise AssertionError("external solver SAT model failed independent clause replay")
        status={True:"SAT",False:"UNSAT",None:"UNKNOWN"}[answer]
    ms=(perf_counter_ns()-start)/1e6
    return CDCLCall(status,int(stats.get("conflicts",0)),int(stats.get("decisions",0)),
                    int(stats.get("propagations",0)),ms,valid)


@dataclass(frozen=True)
class TopologyRecord:
    family: str
    size: int
    seed: int
    digest: str
    features: tuple[float,...]
    null_switches: int
    baseline_ms: float
    signed_plus_null_ms: float
    calls: tuple[CDCLCall,...]
    capped_log_conflicts: float
    capped_log_decisions: float
    censored_calls: int
    median_cdcl_wall_ms: float


def measure_formula(formula: CNFFormula, family: str, size: int, seed: int,
                    *, orbits: int=3, budget: int=2000, swaps: int=160,
                    solver_factory: Callable | None=None) -> TopologyRecord:
    if not 1<=orbits<=8 or family not in FAMILIES:
        raise ValueError("orbit or family budget exceeded")
    features,count,baseline_ns,extra_ns=extract_features(formula,
                                 null_seed=seed*199+size*11+921,swaps=swaps)
    calls=[]
    for i in range(orbits):
        image=(formula if i==0 else _shuffle_vars(formula,
                    Random(seed*100003+size*917+FAMILIES.index(family)*1009+i*37)))
        calls.append(cdcl_call(image,budget=budget,solver_factory=solver_factory))
    resolved={call.status for call in calls if call.status!="UNKNOWN"}
    if len(resolved)>1:
        raise AssertionError("external CDCL disagreeing under equivalent relabelings")
    return TopologyRecord(family,size,seed,canonical_labeled_digest(formula),
         features,count,baseline_ns/1e6,extra_ns/1e6,tuple(calls),
         median(log2(1+min(budget,c.conflicts)) for c in calls),
         median(log2(1+min(budget,c.decisions)) for c in calls),
         sum(c.status=="UNKNOWN" for c in calls),
         median(c.wall_ms for c in calls))


def _predict_ridge(train: Sequence[TopologyRecord],test: Sequence[TopologyRecord],
                   columns: Sequence[str], target: str) -> np.ndarray:
    y=np.array([getattr(x,target) for x in train],dtype=float)
    if not columns:
        return np.full(len(test),float(y.mean()))
    col=[COLS[name] for name in columns]
    X=np.array([[r.features[i] for i in col] for r in train])
    Z=np.array([[r.features[i] for i in col] for r in test])
    mu,sd=X.mean(axis=0),X.std(axis=0)
    sd[sd<1e-12]=1.
    X,Z=(X-mu)/sd,(Z-mu)/sd
    X=np.column_stack((np.ones(len(X)),X))
    Z=np.column_stack((np.ones(len(Z)),Z))
    penalty=np.diag([0.]+[RIDGE_ALPHA]*len(col))
    return Z@np.linalg.solve(X.T@X+penalty,X.T@y)


def _eval_fold(train: Sequence[TopologyRecord],test: Sequence[TopologyRecord],
               target: str) -> dict[str,float]:
    observed=np.array([getattr(x,target) for x in test],dtype=float)
    return {name:float(np.mean(np.abs(_predict_ridge(train,test,features,target)-observed)))
            for name,features in PREDICTORS.items()}


@dataclass(frozen=True)
class Fold:
    label: str
    count: int
    censored_call_fraction: float
    failed_null_fraction: float
    capped_conflict_mae: dict[str,float]
    capped_decision_mae: dict[str,float]


@dataclass(frozen=True)
class TopologyReport:
    seed_count: int
    sizes: tuple[int,...]
    budget: int
    orbits: int
    records: tuple[TopologyRecord,...]
    family_holdouts: tuple[Fold,...]
    size_holdout: Fold | None
    aggregate_family_mae: dict[str,float]
    total_formulas: int
    unique_labeled_formulas: int
    censored_call_fraction: float
    null_nontrivial_fraction: float
    median_baseline_ms: float
    median_signed_increment_ms: float
    median_cdcl_ms: float
    evidence: str="M: budget-capped external CDCL stats; not a SAT certificate"


def _fold(label: str,train: Sequence[TopologyRecord],
          test: Sequence[TopologyRecord]) -> Fold:
    if not train or not test:
        raise ValueError("empty holdout")
    return Fold(label,len(test),
        sum(r.censored_calls for r in test)/sum(len(r.calls) for r in test),
        sum(r.null_switches==0 for r in test)/len(test),
        _eval_fold(train,test,"capped_log_conflicts"),
        _eval_fold(train,test,"capped_log_decisions"))


def topology_benchmark(*,seeds: int=4,sizes: Sequence[int]=(48,72),
                       orbits: int=3,budget: int=2000,swaps: int=160,
                       solver_factory: Callable | None=None) -> TopologyReport:
    if not 2<=seeds<=16 or not sizes or len(set(sizes))!=len(sizes):
        raise ValueError("invalid seed count or size list")
    if any(n<12 or n>144 or n%3 for n in sizes):
        raise ValueError("size must be multiple of 3 between 12 and 144")
    dataset=[]
    for family in FAMILIES:
        for n in sizes:
            for seed in range(seeds):
                formula=generate_formula(family,n,seed)
                dataset.append(measure_formula(formula,family,n,seed,
                    orbits=orbits,budget=budget,swaps=swaps,
                    solver_factory=solver_factory))
    digest_count=len({r.digest for r in dataset})
    if digest_count!=len(dataset):
        raise AssertionError("duplicate labeled CNF: invalid formula split")
    folds=[]
    for heldout in FAMILIES:
        train=[r for r in dataset if r.family!=heldout]
        test=[r for r in dataset if r.family==heldout]
        folds.append(_fold(heldout,train,test))
    size_fold=None
    if len(sizes)>=2:
        largest=max(sizes)
        size_fold=_fold("largest_size="+str(largest),
             [r for r in dataset if r.size!=largest],
             [r for r in dataset if r.size==largest])
    full={name:sum(f.count*f.capped_conflict_mae[name] for f in folds)/len(dataset)
          for name in PREDICTORS}
    return TopologyReport(seeds,tuple(sizes),budget,orbits,tuple(dataset),
        tuple(folds),size_fold,full,len(dataset),digest_count,
        sum(r.censored_calls for r in dataset)/sum(len(r.calls) for r in dataset),
        sum(r.null_switches>0 for r in dataset)/len(dataset),
        median(r.baseline_ms for r in dataset),
        median(r.signed_plus_null_ms for r in dataset),
        median(r.median_cdcl_wall_ms for r in dataset))
