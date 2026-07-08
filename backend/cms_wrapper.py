"""CryptoMiniSat baseline wrapper (pycryptosat) -- a fair competitor to beat.

CryptoMiniSat is the strongest widely-used CDCL solver that also carries a native
GF(2) Gaussian engine, so it OWNS the parity fragment (it is the honest hard case
for our parity frame -- see BEYOND_CDCL_NOTE.md) while remaining a strong general
CDCL. This wrapper runs it on the RAW CNF, exactly as Kissat and CaDiCaL receive it
(no XOR pre-extraction on our side), so the comparison is apples-to-apples: whatever
structure CMS exploits, it finds itself.

It is a BASELINE competitor, not part of the certified path: SAT models are replayed
against the CNF (verify, don't trust), but CMS UNSAT is not DRAT-certified here (the
Python binding does not emit a proof) -- our own certified UNSAT always comes from a
frame refutation or from DRAT-checked Kissat, never from CMS.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from .cnf_utils import CNFFormula, verify_model


@dataclass
class CMSResult:
    status: str                       # 'SAT' | 'UNSAT' | 'TIMEOUT'
    seconds: float
    model: Optional[Dict[int, bool]]  # 1-indexed, when SAT
    verified: bool                    # SAT model replayed against the CNF


def cms_solve(formula: CNFFormula, timeout_s: float = 20.0) -> CMSResult:
    """Solve `formula` with CryptoMiniSat on the raw CNF. Returns a CMSResult; a SAT
    model is independently re-verified. TIMEOUT (or an 'unknown' return) maps to
    status 'TIMEOUT'."""
    from pycryptosat import Solver
    solver = Solver(time_limit=max(1, int(timeout_s)))
    for clause in formula.clauses:
        if clause:                                  # CMS rejects the empty clause add
            solver.add_clause(list(clause))
        else:
            # an explicit empty clause is an immediate refutation
            return CMSResult('UNSAT', 0.0, None, False)
    t0 = time.perf_counter()
    sat, solution = solver.solve()
    dt = time.perf_counter() - t0
    if sat is None:                                 # time/confl limit -> undecided
        return CMSResult('TIMEOUT', dt, None, False)
    if sat:
        # pycryptosat solution is indexed by variable (solution[0] is None); it can
        # be shorter than num_vars+1 when trailing variables never appear in a clause
        # -- those are free, default them to False.
        model = {v: (bool(solution[v]) if v < len(solution) else False)
                 for v in range(1, formula.num_vars + 1)}
        return CMSResult('SAT', dt, model, verify_model(formula, model))
    return CMSResult('UNSAT', dt, None, False)
