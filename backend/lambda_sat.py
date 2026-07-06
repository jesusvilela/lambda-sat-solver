"""lambda_sat -- the honest fusion of the lambda DSL and SAT (Lambda ⊗ SAT).

The operator's Λᴿ ("lambda with remainder") vision, clashed against computation
and reduced to what survives: a Boolean lambda term is *reduced* (lambda motion),
*projected* into CNF (the Boolean shadow, via Tseitin), and *decided*, while a
**remainder** -- a provenance map from each clause back to the lambda node that
produced it -- is preserved (the "ghost fiber"). The satisfying assignment is the
surviving braid; UNSAT is the obstruction.

What survives here is exact and testable. What does NOT survive (curvature /
holonomy / octonionic non-associativity of clauses / zero-divisor scoring) is a
lens, not a decision procedure, and is deliberately absent -- per docs/CHARTER.md,
vocabulary does not enter without a contract.

Honest scope of the "remainder": for a *Boolean* lambda term the Tseitin
projection is equisatisfiable, so the projection loses no *truth* (ε = 0 in the
vision's terms) -- the remainder is **provenance/explanation**, not lost truth.
The vision's living zone `0 < ε < τ` (a remainder that carries active,
unprojected truth) needs a non-Boolean payload (types, uncertainty) and is
future work, not claimed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

from .cnf_utils import CNFFormula, verify_model


# --------------------------------------------------------------------------
# Boolean lambda calculus (object level)
# --------------------------------------------------------------------------
class BExpr:
    """Boolean lambda expression."""


@dataclass(frozen=True)
class BVar(BExpr):
    name: str


@dataclass(frozen=True)
class BConst(BExpr):
    value: bool


@dataclass(frozen=True)
class BNot(BExpr):
    e: BExpr


@dataclass(frozen=True)
class BAnd(BExpr):
    l: BExpr
    r: BExpr


@dataclass(frozen=True)
class BOr(BExpr):
    l: BExpr
    r: BExpr


@dataclass(frozen=True)
class Lam(BExpr):
    param: str
    body: BExpr


@dataclass(frozen=True)
class App(BExpr):
    fn: BExpr
    arg: BExpr


def free_vars(e: BExpr) -> Set[str]:
    if isinstance(e, BVar):
        return {e.name}
    if isinstance(e, BConst):
        return set()
    if isinstance(e, BNot):
        return free_vars(e.e)
    if isinstance(e, (BAnd, BOr)):
        return free_vars(e.l) | free_vars(e.r)
    if isinstance(e, Lam):
        return free_vars(e.body) - {e.param}
    if isinstance(e, App):
        return free_vars(e.fn) | free_vars(e.arg)
    raise TypeError(e)


def _subst(e: BExpr, name: str, val: BExpr) -> BExpr:
    if isinstance(e, BVar):
        return val if e.name == name else e
    if isinstance(e, BConst):
        return e
    if isinstance(e, BNot):
        return BNot(_subst(e.e, name, val))
    if isinstance(e, BAnd):
        return BAnd(_subst(e.l, name, val), _subst(e.r, name, val))
    if isinstance(e, BOr):
        return BOr(_subst(e.l, name, val), _subst(e.r, name, val))
    if isinstance(e, Lam):
        return e if e.param == name else Lam(e.param, _subst(e.body, name, val))
    if isinstance(e, App):
        return App(_subst(e.fn, name, val), _subst(e.arg, name, val))
    raise TypeError(e)


def beta_normalize(e: BExpr, max_steps: int = 100_000) -> BExpr:
    """Reduce applications of abstractions; raise on step-budget exhaustion."""
    steps = 0

    def step(x: BExpr) -> Tuple[BExpr, bool]:
        nonlocal steps
        if isinstance(x, App):
            fn, changed = step(x.fn)
            if changed:
                return App(fn, x.arg), True
            if isinstance(fn, Lam):
                steps += 1
                if steps > max_steps:
                    raise RuntimeError("beta reduction did not terminate")
                return _subst(fn.body, fn.param, x.arg), True
            arg, changed = step(x.arg)
            return App(fn, arg), changed
        if isinstance(x, BNot):
            b, c = step(x.e)
            return BNot(b), c
        if isinstance(x, BAnd):
            l, c = step(x.l)
            if c:
                return BAnd(l, x.r), True
            r, c = step(x.r)
            return BAnd(x.l, r), c
        if isinstance(x, BOr):
            l, c = step(x.l)
            if c:
                return BOr(l, x.r), True
            r, c = step(x.r)
            return BOr(x.l, r), c
        if isinstance(x, Lam):
            b, c = step(x.body)
            return Lam(x.param, b), c
        return x, False

    cur = e
    while True:
        cur, changed = step(cur)
        if not changed:
            return cur


def eval_bool(e: BExpr, assignment: Dict[str, bool]) -> bool:
    """Evaluate a beta-normal Boolean expression (no Lam/App) under an
    assignment of its free variables."""
    if isinstance(e, BConst):
        return e.value
    if isinstance(e, BVar):
        return assignment[e.name]
    if isinstance(e, BNot):
        return not eval_bool(e.e, assignment)
    if isinstance(e, BAnd):
        return eval_bool(e.l, assignment) and eval_bool(e.r, assignment)
    if isinstance(e, BOr):
        return eval_bool(e.l, assignment) or eval_bool(e.r, assignment)
    raise ValueError(f"not beta-normal / not Boolean: {type(e).__name__}")


# --------------------------------------------------------------------------
# Projection into CNF (Tseitin) with a remainder (provenance)
# --------------------------------------------------------------------------
def tseitin_encode(e: BExpr) -> Tuple[CNFFormula, Dict[int, str], Dict[str, int]]:
    """Tseitin-encode a beta-normal Boolean expression, asserting the whole
    expression true. Returns (cnf, remainder, free_var_ids) where `remainder`
    maps each clause index to the lambda node that produced it -- the ghost
    fiber linking the Boolean shadow back to its source."""
    clauses: List[List[int]] = []
    remainder: Dict[int, str] = {}
    free_ids: Dict[str, int] = {}
    counter = [0]

    def fresh() -> int:
        counter[0] += 1
        return counter[0]

    def emit(clause: List[int], src: str) -> None:
        remainder[len(clauses)] = src
        clauses.append(clause)

    def enc(x: BExpr) -> int:
        """Return a literal whose truth equals the value of x."""
        if isinstance(x, BConst):
            v = fresh()
            emit([v] if x.value else [-v], f"const:{x.value}")
            return v
        if isinstance(x, BVar):
            if x.name not in free_ids:
                free_ids[x.name] = fresh()
            return free_ids[x.name]
        if isinstance(x, BNot):
            return -enc(x.e)
        if isinstance(x, BAnd):
            a, b = enc(x.l), enc(x.r)
            g = fresh()
            emit([-g, a], "and"); emit([-g, b], "and"); emit([g, -a, -b], "and")
            return g
        if isinstance(x, BOr):
            a, b = enc(x.l), enc(x.r)
            g = fresh()
            emit([g, -a], "or"); emit([g, -b], "or"); emit([-g, a, b], "or")
            return g
        raise ValueError(f"not beta-normal / not Boolean: {type(x).__name__}")

    top = enc(e)
    emit([top], "assert-true")     # the whole term must evaluate true
    return CNFFormula(num_vars=counter[0], clauses=clauses), remainder, free_ids


# --------------------------------------------------------------------------
# The fusion: reduce -> project -> decide -> certify, remainder preserved
# --------------------------------------------------------------------------
@dataclass
class LambdaSatResult:
    status: str                          # 'SAT' | 'UNSAT'
    witness: Optional[Dict[str, bool]]   # free-var assignment making the term true
    free_vars: List[str]
    cnf: CNFFormula                      # the Boolean-shadow projection
    remainder: Dict[int, str]            # clause index -> source lambda node
    projection_faithful: Optional[bool]  # CNF-SAT iff source-SAT (verified small)


def lambda_sat(term: BExpr, max_free: int = 20) -> LambdaSatResult:
    """Clash a Boolean lambda term against SAT. Beta-normalize (lambda motion),
    decide satisfiability at the source (certified by direct evaluation -- the
    surviving braid), project into CNF carrying the remainder, and cross-check
    that the projection preserved truth (equisatisfiable, small instances)."""
    normal = beta_normalize(term)
    fv = sorted(free_vars(normal))
    if len(fv) > max_free:
        raise ValueError(f"too many free variables ({len(fv)} > {max_free})")

    # decision at the source: is there an assignment making the term true?
    witness: Optional[Dict[str, bool]] = None
    for bits in product([False, True], repeat=len(fv)):
        a = dict(zip(fv, bits))
        if eval_bool(normal, a):
            witness = a
            break
    status = 'SAT' if witness is not None else 'UNSAT'
    # certify a SAT witness by re-evaluation (verify, don't trust the search)
    if witness is not None:
        assert eval_bool(normal, witness)

    cnf, remainder, free_ids = tseitin_encode(normal)

    # faithfulness: the projection is SAT iff the source is SAT (verified by
    # brute force on the CNF for small instances; None if too large to check)
    faithful: Optional[bool] = None
    if cnf.num_vars <= 22:
        cnf_sat = False
        for bits in product([False, True], repeat=cnf.num_vars):
            m = {i + 1: bits[i] for i in range(cnf.num_vars)}
            if verify_model(cnf, m):
                cnf_sat = True
                break
        faithful = (cnf_sat == (status == 'SAT'))

    return LambdaSatResult(status, witness, fv, cnf, remainder, faithful)
