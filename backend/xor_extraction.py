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

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from .cnf_utils import CNFFormula, verify_model


@dataclass
class XORConstraint:
    variables: Tuple[int, ...]   # sorted positive variable ids
    rhs: int                     # 0 or 1 : x_v1 ^ ... ^ x_vk = rhs


@dataclass
class XORExtractionResult:
    xors: List[XORConstraint]
    num_xor_clauses: int         # distinct clauses belonging to a recovered XOR
    xor_clause_fraction: float   # num_xor_clauses / total clauses (frame signal)


def extract_xors(formula: CNFFormula, max_arity: int = 6) -> XORExtractionResult:
    """Recover complete XOR groups of arity 2..max_arity. Cost is
    O(clauses * arity) plus the group bookkeeping; max_arity caps the 2^(k-1)
    blow-up (mirrors real solvers, which only recover short XORs)."""
    # collect the distinct sign patterns present for each variable set
    patterns_by_varset: Dict[frozenset, Set[Tuple[bool, ...]]] = {}
    for clause in formula.clauses:
        vs = [abs(l) for l in clause]
        k = len(vs)
        if k < 2 or k > max_arity:
            continue
        if len(set(vs)) != k:
            continue  # a repeated variable / tautology is not a clean XOR clause
        varset = frozenset(vs)
        order = sorted(varset)
        sign = {abs(l): (l > 0) for l in clause}
        pattern = tuple(sign[v] for v in order)
        patterns_by_varset.setdefault(varset, set()).add(pattern)

    xors: List[XORConstraint] = []
    num_xor_clauses = 0
    for varset, patterns in patterns_by_varset.items():
        k = len(varset)
        full = 1 << (k - 1)
        by_parity: Dict[int, int] = {0: 0, 1: 0}
        for pat in patterns:
            n_neg = sum(1 for positive in pat if not positive)
            by_parity[n_neg & 1] += 1
        order = tuple(sorted(varset))
        for c, count in by_parity.items():
            if count == full:            # a complete parity group
                xors.append(XORConstraint(order, rhs=1 - c))
                num_xor_clauses += full

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
