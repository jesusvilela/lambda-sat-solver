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

from .cnf_utils import CNFFormula


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
