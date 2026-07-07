"""lambda_sat -- the honest fusion of the lambda DSL and SAT (Lambda ⊗ SAT).

A Boolean lambda term is *reduced* (lambda motion), *projected* into CNF (the
Boolean shadow) carrying a **remainder** -- a provenance map from each clause
back to the lambda node that produced it (the "ghost fiber") -- and *decided*.

Meta-resolution (the second half of the operator's "self-resolve AND meta-resolve
contradiction"): the fusion does not merely brute-force the term. It first asks
*which frame* collapses the term's contradiction. When the beta-normal form is a
**parity system**, it is encoded frame-native (parity clause groups over the
original variables, no auxiliary gates) so the GF(2) frame recognizes it, and the
term is decided in the parity frame -- polynomial, certified, no enumeration. The
`resolved_by` field records the frame that collapsed it. Otherwise the term is
gate-encoded; the sound frames are still tried on the projection, and anything
they cannot decide falls to a brute-force source decision with a re-verified
witness (verify, don't trust).

Honest scope of the remainder: for a *Boolean* term the projection is
equisatisfiable, so the remainder is provenance (ε = 0), not lost truth. The
frame-native parity encoding is even cleaner -- no auxiliary variables, so the
Boolean shadow *is* the algebraic object, and its GF(2) UNSAT is exactly the
refutation whose soundness is stated in `proofs/XorSoundness.lean`. The living
zone ε > 0 (a remainder carrying active, unprojected truth) needs a richer-than-
Boolean payload and remains the next contract, per docs/CHARTER.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

from .binary_clause_check import check_binary_clauses
from .cardinality_check import pigeonhole_counting_refutation
from .cnf_utils import CNFFormula, verify_model
from .xor_extraction import _rref_gf2, gf2_xor_refutation


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
class BXor(BExpr):
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
    if isinstance(e, (BAnd, BOr, BXor)):
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
    if isinstance(e, BXor):
        return BXor(_subst(e.l, name, val), _subst(e.r, name, val))
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
        if isinstance(x, (BAnd, BOr, BXor)):
            l, c = step(x.l)
            if c:
                return type(x)(l, x.r), True
            r, c = step(x.r)
            return type(x)(x.l, r), c
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
    if isinstance(e, BXor):
        return eval_bool(e.l, assignment) != eval_bool(e.r, assignment)
    raise ValueError(f"not beta-normal / not Boolean: {type(e).__name__}")


# --------------------------------------------------------------------------
# Frame recognition: is the beta-normal term a parity system?
# --------------------------------------------------------------------------
def _xor_atom(e: BExpr) -> Optional[Tuple[frozenset, int]]:
    """If e is an XOR/negation combination of literals, return (varset, const)
    with value(e) = XOR_{v in varset}(v) XOR const; else None."""
    if isinstance(e, BConst):
        return frozenset(), (1 if e.value else 0)
    if isinstance(e, BVar):
        return frozenset({e.name}), 0
    if isinstance(e, BNot):
        r = _xor_atom(e.e)
        return None if r is None else (r[0], r[1] ^ 1)
    if isinstance(e, BXor):
        a, b = _xor_atom(e.l), _xor_atom(e.r)
        if a is None or b is None:
            return None
        return (a[0] ^ b[0]), (a[1] ^ b[1])   # symmetric diff of vars, xor consts
    return None


# a parity constraint XOR(varset) = rhs; empty varset with rhs 1 is 0=1 (UNSAT)
ParityAtom = Tuple[frozenset, int]


def _as_parity_atoms(e: BExpr) -> Optional[List[ParityAtom]]:
    """Express 'e is true' as a conjunction of parity constraints, or None if e
    is not a conjunction of XOR-over-literals."""
    if isinstance(e, BAnd):
        left = _as_parity_atoms(e.l)
        if left is None:
            return None
        right = _as_parity_atoms(e.r)
        if right is None:
            return None
        return left + right
    atom = _xor_atom(e)
    if atom is None:
        return None
    varset, const = atom
    return [(varset, 1 ^ const)]           # value == 1  <=>  XOR(varset) = 1^const


def _parity_clauses(vs: List[int], rhs: int) -> List[List[int]]:
    """CNF for XOR(vs) = rhs: the 2^(k-1) clauses of the wrong parity."""
    out = []
    for bits in product([0, 1], repeat=len(vs)):
        if sum(bits) % 2 != rhs:
            out.append([(v if b == 0 else -v) for v, b in zip(vs, bits)])
    return out


#: budget on the *materialized* frame-native parity CNF kept for provenance. The
#: parity decision itself runs on GF(2) rows (polynomial, any arity); we only
#: build the 2^(k-1)-clause shadow for the ghost fiber when it stays this small.
_PARITY_CNF_BUDGET = 4096


def _parity_provenance_cnf(atoms: List[ParityAtom], var_id: Dict[str, int],
                           n: int) -> Tuple[CNFFormula, Dict[int, str]]:
    """Frame-native parity CNF (clause index -> "parity") for the ghost fiber,
    but only when the total 2^(k-1) blow-up stays within `_PARITY_CNF_BUDGET`.
    Beyond it the algebraic object is the GF(2) rows, not their exponential CNF
    shadow, so we return an empty projection rather than materialize it."""
    total = sum(1 << (len(vs) - 1) for vs, _ in atoms if vs)
    if total > _PARITY_CNF_BUDGET:
        return CNFFormula(num_vars=n, clauses=[]), {}
    clauses: List[List[int]] = []
    remainder: Dict[int, str] = {}
    for varset, rhs in atoms:
        if not varset:
            continue
        for cl in _parity_clauses(sorted(var_id[v] for v in varset), rhs):
            remainder[len(clauses)] = "parity"
            clauses.append(cl)
    return CNFFormula(num_vars=n, clauses=clauses), remainder


# --------------------------------------------------------------------------
# Gate (Tseitin) projection with a remainder, for non-parity terms
# --------------------------------------------------------------------------
def tseitin_encode(e: BExpr) -> Tuple[CNFFormula, Dict[int, str], Dict[str, int]]:
    """Tseitin-encode a beta-normal Boolean expression, asserting it true.
    Returns (cnf, remainder, free_var_ids); `remainder` maps clause index to
    the lambda node that produced it -- the ghost fiber."""
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
        if isinstance(x, BXor):
            a, b = enc(x.l), enc(x.r)
            g = fresh()
            emit([-a, -b, -g], "xor"); emit([a, b, -g], "xor")
            emit([a, -b, g], "xor"); emit([-a, b, g], "xor")
            return g
        raise ValueError(f"not beta-normal / not Boolean: {type(x).__name__}")

    top = enc(e)
    emit([top], "assert-true")
    return CNFFormula(num_vars=counter[0], clauses=clauses), remainder, free_ids


# --------------------------------------------------------------------------
# The fusion: reduce -> recognize frame -> decide (meta-resolve) -> certify
# --------------------------------------------------------------------------
@dataclass
class LambdaSatResult:
    status: str                          # 'SAT' | 'UNSAT'
    witness: Optional[Dict[str, bool]]   # free-var assignment making the term true
    free_vars: List[str]
    resolved_by: str                     # 'parity' | '2sat' | 'counting' | 'direct'
    cnf: CNFFormula                      # the projection (frame-native or gates)
    remainder: Dict[int, str]            # clause index -> source / frame tag
    projection_faithful: Optional[bool]  # CNF-SAT iff source-SAT (verified small)


def _brute_cnf_sat(cnf: CNFFormula) -> bool:
    for bits in product([False, True], repeat=cnf.num_vars):
        if verify_model(cnf, {i + 1: bits[i] for i in range(cnf.num_vars)}):
            return True
    return False


def lambda_sat(term: BExpr, max_free: int = 20) -> LambdaSatResult:
    """Clash a Boolean lambda term against SAT and let the shallowest frame
    collapse it. Beta-normalize; if the normal form is a parity system, decide
    it in the GF(2) frame (frame-native, certified); otherwise gate-encode, try
    the sound frames, and fall to a re-verified brute-force source decision."""
    normal = beta_normalize(term)
    fv = sorted(free_vars(normal))
    if len(fv) > max_free:
        raise ValueError(f"too many free variables ({len(fv)} > {max_free})")
    var_id = {name: i + 1 for i, name in enumerate(fv)}

    def direct_witness() -> Optional[Dict[str, bool]]:
        for bits in product([False, True], repeat=len(fv)):
            a = dict(zip(fv, bits))
            if eval_bool(normal, a):
                return a
        return None

    # ---- meta-resolution 1: the parity frame (frame-native, no aux gates) ----
    atoms = _as_parity_atoms(normal)
    if atoms is not None:
        n = len(fv)
        # Decide the parity system DIRECTLY as GF(2) rows over the free-var ids:
        # each atom (varset, rhs) is one row (bit per variable, rhs at bit n).
        # No 2^(k-1) CNF materialization and no arity cap -- this is what makes
        # the parity frame actually polynomial (a single k-XOR is ONE row, not
        # its 2^(k-1)-clause shadow re-extracted through a max_arity filter).
        rows: List[int] = []
        immediate_unsat = False
        for varset, rhs in atoms:
            if not varset:                          # 0 = rhs
                if rhs == 1:
                    immediate_unsat = True
                continue
            row = 0
            for v in varset:
                row |= 1 << (var_id[v] - 1)
            if rhs:
                row |= 1 << n
            rows.append(row)

        cnf, remainder = _parity_provenance_cnf(atoms, var_id, n)  # ghost fiber
        if immediate_unsat:
            return LambdaSatResult('UNSAT', None, fv, 'parity', cnf,
                                   remainder, True)

        basis = _rref_gf2(rows, n)                   # tested GF(2) elimination
        if basis is None:
            return LambdaSatResult('UNSAT', None, fv, 'parity', cnf,
                                   remainder, True)
        # consistent: free vars := False, pivot vars := their reduced rhs bit
        assign = {c: False for c in range(n)}
        for pivot_col, row in basis.items():
            assign[pivot_col] = bool((row >> n) & 1)
        witness = {v: assign[var_id[v] - 1] for v in fv}
        assert eval_bool(normal, witness)            # verify, don't trust
        return LambdaSatResult('SAT', witness, fv, 'parity', cnf,
                               remainder, True)

    # ---- otherwise: gate projection + try the sound frames, else direct ----
    cnf, remainder, _ = tseitin_encode(normal)
    if not check_binary_clauses(cnf).consistent:
        return LambdaSatResult('UNSAT', None, fv, '2sat', cnf, remainder, None)
    if gf2_xor_refutation(cnf).refuted:
        return LambdaSatResult('UNSAT', None, fv, 'parity', cnf, remainder, None)
    if pigeonhole_counting_refutation(cnf).refuted:
        return LambdaSatResult('UNSAT', None, fv, 'counting', cnf, remainder, None)

    witness = direct_witness()
    status = 'SAT' if witness is not None else 'UNSAT'
    if witness is not None:
        assert eval_bool(normal, witness)
    faithful = None
    if cnf.num_vars <= 22:
        faithful = (_brute_cnf_sat(cnf) == (status == 'SAT'))
    return LambdaSatResult(status, witness, fv, 'direct', cnf, remainder, faithful)


# --------------------------------------------------------------------------
# The Y-combinator spine: bounded fixpoint unrolling, and the living remainder
# --------------------------------------------------------------------------
# Full Y (`Y f = f (Y f)`) is undecidable -- a certificate cannot exist for the
# general fixpoint. Its decidable spine is *bounded* unrolling: expand the
# fixpoint of `lam = λs. body` to depth k, leaving the un-reached tail as a free
# variable. That tail is the operator's remainder made literal: if the depth-k
# decision still depends on the tail, the fixpoint has NOT been pinned down --
# ε > 0, the remainder is active. If it is independent of the tail, the fixpoint
# stabilized by depth k -- ε = 0. The pure self-negation `λs. ¬s` (the Möbius
# fixpoint: traverse once, return flipped) never stabilizes: its remainder is
# eternally nonzero.

FIX_TAIL = "__fix_tail__"


def unroll_fix(lam: "Lam", depth: int, tail_name: str = FIX_TAIL) -> BExpr:
    """Unroll the fixpoint of `λs. body` to `depth`, with the un-reached tail as
    the free variable `tail_name`: body[s := body[s := ... [s := tail]]]."""
    if not isinstance(lam, Lam):
        raise TypeError("unroll_fix expects a Lam (λs. body)")
    result: BExpr = BVar(tail_name)
    for _ in range(depth):
        result = _subst(lam.body, lam.param, result)
    return result


@dataclass
class FixResult:
    depth: int
    tail: str
    remainder_active: bool               # ε > 0 : the depth-k truth depends on the tail
    decision: LambdaSatResult            # decision of the unrolled Boolean term


def fixpoint_sat(lam: "Lam", depth: int, max_free: int = 20) -> FixResult:
    """Decide the depth-`depth` unrolling of a Boolean fixpoint and measure
    whether its remainder (the tail boundary) is still active (ε > 0)."""
    tail = FIX_TAIL
    unrolled = beta_normalize(unroll_fix(lam, depth, tail))
    others = sorted(free_vars(unrolled) - {tail})
    active = False
    for bits in product([False, True], repeat=len(others)):
        a = dict(zip(others, bits))
        if eval_bool(unrolled, {**a, tail: False}) != \
                eval_bool(unrolled, {**a, tail: True}):
            active = True          # flipping the boundary changes the truth
            break
    return FixResult(depth, tail, active, lambda_sat(unrolled, max_free=max_free))
