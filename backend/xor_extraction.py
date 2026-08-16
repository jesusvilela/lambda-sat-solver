"""XOR / parity structure recovery from CNF (the GF(2) frame detector).

The cheap, poly-time shadow of `backend.complexity.cross_algebra_depth`. That
demonstrator showed (via the exponential obstruction depths) that a formula's
"shallow frame" is algebra-relative: Tseitin is shallow in GF(2) linear algebra
(low Nullstellensatz degree) but deep in resolution (high width), while PHP is
the reverse. The GF(2) frame is shallow exactly when the formula carries genuine
parity/XOR structure, and *that* is detectable in polynomial time -- unlike the
depths themselves.

This module recovers XOR constraints encoded in CNF, the sibling of
`binary_clause_check` (which detects the 2-SAT frame). Real solvers do the same
(CryptoMiniSat recovers XORs and runs Gaussian elimination on them). It is a
frame *discriminator*, not a solver: a high `xor_clause_fraction` says "the
algebraic frame is the shallow one here" -- the practical, cheap form of the
shallow-Emperor hunt.

Encoding recovered: a parity constraint x_{i1} XOR ... XOR x_{ik} = r over a
variable set V of size k is encoded as exactly 2^(k-1) clauses, all over V (each
variable appearing once), whose count of negative literals has a fixed parity c;
that group encodes rhs r = 1 - c. We detect a full such group.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from .cnf_utils import CNFFormula, verify_model

try:                                    # numpy is already a core backend dep
    import numpy as _np
    _HAS_NUMPY = True
except Exception:                       # keep the module importable without it
    _HAS_NUMPY = False

#: below this many clauses in an arity bucket, numpy's array/unique overhead is
#: not worth it -- use the pure-Python path (which is also the trusted spec).
_VEC_MIN_ROWS = 64


@dataclass
class XORConstraint:
    variables: Tuple[int, ...]   # sorted positive variable ids
    rhs: int                     # 0 or 1 : x_v1 ^ ... ^ x_vk = rhs


@dataclass
class XORExtractionResult:
    xors: List[XORConstraint]
    num_xor_clauses: int         # distinct clauses belonging to a recovered XOR
    xor_clause_fraction: float   # num_xor_clauses / total clauses (frame signal)


def _bucket_python(rows: List[List[int]], k: int) -> List[Tuple[Tuple[int, ...], int]]:
    """Reference (trusted spec) recovery within one fixed-arity bucket.

    For each variable set collect its distinct sign patterns, each encoded as a
    k-bit int (bit i set iff the i-th variable in sorted order is negated) and
    pre-split by the parity of the negation count. A complete parity group of
    arity k is exactly 2^(k-1) distinct patterns all sharing one negation-parity
    c; that group encodes rhs = 1 - c. Returns (order, rhs) for each such group.
    """
    patterns: Dict[Tuple[int, ...], Tuple[Set[int], Set[int]]] = {}
    for clause in rows:
        pairs = sorted((abs(l), l > 0) for l in clause)   # one sort per clause
        order = tuple(p[0] for p in pairs)
        # repeated variable / tautology -> adjacent equal vars after the sort
        if any(order[i] == order[i + 1] for i in range(k - 1)):
            continue
        bits = 0
        neg = 0
        for i, (_, positive) in enumerate(pairs):
            if not positive:
                bits |= 1 << i
                neg += 1
        slot = patterns.get(order)
        if slot is None:
            slot = patterns[order] = (set(), set())
        slot[neg & 1].add(bits)

    full = 1 << (k - 1)
    out: List[Tuple[Tuple[int, ...], int]] = []
    for order, (parity0, parity1) in patterns.items():
        if len(parity0) == full:         # c=0 -> rhs 1
            out.append((order, 1))
        if len(parity1) == full:         # c=1 -> rhs 0
            out.append((order, 0))
    return out


def _bucket_vectorized(rows: List[List[int]], k: int,
                       bits: int) -> List[Tuple[Tuple[int, ...], int]]:
    """Vectorized recovery within one fixed-arity bucket: the whole bucket lives
    as one dense (m, k) int tensor, and abs / per-row sort / sign-encode / parity
    all run as array ops -- `np.unique` is the 'compact identical patterns into
    one point' step (distinct sign patterns per group collapse to unique rows).

    Numerically identical to `_bucket_python` (differential-tested). Caller must
    guarantee `bits * k <= 62` so the packed varset key fits a signed int64.
    """
    A = _np.array(rows, dtype=_np.int64)             # signed literals
    V = _np.abs(A)
    if k > 1:                                        # drop dup-var / tautology
        Vs = _np.sort(V, axis=1)
        A = A[~(Vs[:, 1:] == Vs[:, :-1]).any(axis=1)]
        if A.shape[0] == 0:
            return []
        V = _np.abs(A)
    idx = _np.argsort(V, axis=1, kind="stable")      # canonical: sort by var
    Asort = A[_np.arange(A.shape[0])[:, None], idx]
    Vsort = _np.abs(Asort)
    neg = Asort < 0
    key = (Vsort * (1 << (bits * _np.arange(k))).astype(_np.int64)).sum(axis=1)
    patbits = (neg.astype(_np.int64) << _np.arange(k)).sum(axis=1)
    parity = neg.sum(axis=1) & 1
    group = key * 2 + parity                         # (varset, neg-parity)
    distinct = _np.unique(_np.stack([group, patbits], axis=1), axis=0)
    groups, counts = _np.unique(distinct[:, 0], return_counts=True)
    full = 1 << (k - 1)
    mask = (1 << bits) - 1
    out: List[Tuple[Tuple[int, ...], int]] = []
    for g, cnt in zip(groups.tolist(), counts.tolist()):
        if cnt == full:                              # a complete parity group
            keyv, par = g >> 1, g & 1
            order = tuple((keyv >> (bits * i)) & mask for i in range(k))
            out.append((order, 1 - par))
    return out


def extract_xors(formula: CNFFormula, max_arity: int = 6) -> XORExtractionResult:
    """Recover complete XOR groups of arity 2..max_arity. Cost is
    O(clauses * arity) plus the group bookkeeping; max_arity caps the 2^(k-1)
    blow-up (mirrors real solvers, which only recover short XORs).

    Clauses are bucketed by arity so each bucket is a dense fixed-width tensor;
    a bucket with enough clauses (and whose packed key fits int64) is recovered
    vectorized (~1.7x on Tseitin, more on ragged CNF -- measured in
    docs/ladder/scripts/frame_router_scaling.py), otherwise by the pure-Python
    reference. The two paths are differential-tested to agree exactly
    (test_xor_extraction), so the vectorized fast path never widens the trusted
    base: extraction correctness (a spurious XOR would be an unsound refutation)
    still rests on the readable spec, which also runs whenever numpy is absent.
    """
    buckets: Dict[int, List[List[int]]] = defaultdict(list)
    for clause in formula.clauses:
        k = len(clause)
        if 2 <= k <= max_arity:
            buckets[k].append(clause)

    bits = max(1, int(formula.num_vars).bit_length())
    completed: List[Tuple[Tuple[int, ...], int]] = []
    for k, rows in buckets.items():
        if _HAS_NUMPY and bits * k <= 62 and len(rows) >= _VEC_MIN_ROWS:
            completed += _bucket_vectorized(rows, k, bits)
        else:
            completed += _bucket_python(rows, k)

    xors = [XORConstraint(order, rhs) for order, rhs in completed]
    num_xor_clauses = sum(1 << (len(order) - 1) for order, _ in completed)

    total = len(formula.clauses)
    fraction = num_xor_clauses / total if total else 0.0
    return XORExtractionResult(xors, num_xor_clauses, fraction)


@dataclass
class XORRefutation:
    refuted: bool                # True => formula is UNSAT (sound certificate)
    num_xors: int
    decides_fully: bool          # recovered XORs cover the whole formula


def gf2_xor_refutation(formula: CNFFormula, max_arity: int = 6) -> XORRefutation:
    """Sound partial UNSAT certificate from the XOR/parity clauses, via Gaussian
    elimination over GF(2). The algebraic sibling of `binary_clause_check` (which
    refutes from the 2-SAT clauses): both are cheap, engine-independent fast paths
    that decide exactly the fragment where their frame is shallow.

    If `refuted` is True the formula is UNSAT -- the recovered XORs are logically
    entailed (each is the exact CNF encoding of its parity constraint), so an
    inconsistent XOR subsystem refutes the whole formula. If `refuted` is False,
    this is inconclusive (fall through to CDCL) unless `decides_fully` is also
    True, in which case the formula is SAT on its (all-parity) structure.

    Benchmark (docs/ladder/FRAME_BENCHMARK_REPORT.md): on Tseitin-expander
    instances this returns in << 1 ms where Kissat and CaDiCaL both time out.
    """
    res = extract_xors(formula, max_arity=max_arity)
    n = formula.num_vars
    pivots: Dict[int, int] = {}
    refuted = False
    for x in res.xors:
        row = 0
        for v in x.variables:
            row |= (1 << (v - 1))
        if x.rhs:
            row |= (1 << n)
        cur = row
        while cur:
            lead = (cur & -cur).bit_length() - 1
            if lead == n:                # reduced to 0 = 1
                refuted = True
                break
            if lead in pivots:
                cur ^= pivots[lead]
            else:
                pivots[lead] = cur
                break
        if refuted:
            break
    return XORRefutation(refuted, len(res.xors), res.xor_clause_fraction >= 0.999)


@dataclass
class XORSolveResult:
    status: str                        # 'SAT' | 'UNSAT' | 'INCONCLUSIVE'
    model: Optional[Dict[int, bool]]   # 1-indexed assignment, only when SAT
    decides_fully: bool                # recovered XORs cover the whole formula


def _rref_gf2(rows: List[int], n: int):
    """Reduced row-echelon form over GF(2). Rows are ints: bits 0..n-1 are
    variables, bit n is the rhs. Returns a dict pivot_col -> reduced row, or
    None if the system is inconsistent (some row reduces to 0 = 1)."""
    var_mask = (1 << n) - 1
    basis: Dict[int, int] = {}
    for r in rows:
        cur = r
        for col, brow in basis.items():        # eliminate known pivot columns
            if (cur >> col) & 1:
                cur ^= brow
        if (cur & var_mask) == 0:              # variable part vanished
            if cur == 0:
                continue                        # dependent row
            return None                         # 0 = 1  -> inconsistent
        pivot_col = ((cur & var_mask) & -(cur & var_mask)).bit_length() - 1
        for col in list(basis):                 # keep existing rows reduced
            if (basis[col] >> pivot_col) & 1:
                basis[col] ^= cur
        basis[pivot_col] = cur
    return basis


def gf2_xor_solve(formula: CNFFormula, max_arity: int = 6) -> XORSolveResult:
    """Complete the frame router's SAT side: decide a parity-structured formula
    in the GF(2) frame by Gaussian elimination, and (when the recovered XORs
    cover the whole formula) reconstruct a satisfying assignment.

    - inconsistent XOR system  -> 'UNSAT' (sound for ANY formula: XORs entailed)
    - consistent AND fully covered -> 'SAT' with a model, INDEPENDENTLY verified
      against the original CNF via verify_model (Charter: verify, don't trust)
    - otherwise -> 'INCONCLUSIVE' (fall through to CDCL): either the parity core
      is satisfiable but does not cover the formula, or (defensively) a
      reconstructed model failed verification.

    This is the poly-time algebraic decision for the pure-parity frame — the SAT
    counterpart of gf2_xor_refutation, closing the loop the frame benchmark
    opened (UNSAT side only).
    """
    res = extract_xors(formula, max_arity=max_arity)
    n = formula.num_vars
    covered = res.xor_clause_fraction >= 0.999
    rows = []
    for x in res.xors:
        row = 0
        for v in x.variables:
            row |= (1 << (v - 1))
        if x.rhs:
            row |= (1 << n)
        rows.append(row)

    basis = _rref_gf2(rows, n)
    if basis is None:
        return XORSolveResult('UNSAT', None, covered)   # sound regardless of coverage
    if not covered:
        return XORSolveResult('INCONCLUSIVE', None, False)

    # consistent + fully covered: free variables := False, pivots := rhs bit
    model = {v: False for v in range(1, n + 1)}
    for pivot_col, row in basis.items():
        model[pivot_col + 1] = bool((row >> n) & 1)
    if verify_model(formula, model):
        return XORSolveResult('SAT', model, True)
    return XORSolveResult('INCONCLUSIVE', None, True)   # defensive: never claim unverified SAT
