"""frame_solver -- the crystallized frame router (the session's distilled result).

The whole research arc reduces to one usable procedure: given a CNF, ask *which
sound algebraic frame collapses its contradiction* before handing it to CDCL. The
three frames are each sound and poly-time; a formula that lives in one is decided
with a certificate and no search. Only what escapes all three needs a CDCL engine.

    implication (2-SAT)  -> check_binary_clauses   (sound UNSAT)
    parity (GF(2))       -> gf2_xor_solve          (UNSAT sound; SAT model-verified)
    counting (ℤ)         -> pigeonhole_counting     (sound UNSAT)
    else                 -> CDCL_NEEDED             (hand to Kissat + certify)

Measured (docs/ladder/METAL_ROADMAP.md): the UNSAT path is near-linear -- ~36 ms
end-to-end at 4500 variables in pure Python (2-SAT scan + parsing + the sound
GF(2) refutation), the Gaussian core near-free. The SAT path pays a full RREF to
rebuild a model and is superlinear (~1.1 s at 4500 vars), which is why the router
refutes *before* it reconstructs. No metal rewrite is justified at research
scale; this module is the honest crystal -- the geometry's job is to find the
flat frame, and here it is, as one call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .binary_clause_check import check_binary_clauses
from .cardinality_check import pigeonhole_counting_refutation
from .cnf_utils import CNFFormula, verify_model
from .xor_extraction import gf2_xor_refutation, gf2_xor_solve


@dataclass
class FrameResult:
    status: str                       # 'SAT' | 'UNSAT' | 'CDCL_NEEDED'
    resolved_by: str                  # '2sat' | 'parity' | 'counting' | 'none'
    certified: bool                   # frame verdicts are sound-by-construction /
                                      # model-verified; CDCL_NEEDED is neither
    model: Optional[Dict[int, bool]]  # 1-indexed assignment when status == 'SAT'


def frame_solve(formula: CNFFormula) -> FrameResult:
    """Decide `formula` in the shallowest sound frame that collapses it, or
    report `CDCL_NEEDED`. Every 'SAT'/'UNSAT' returned here is certified: UNSAT
    by a sound refutation (2-SAT SCC, GF(2) inconsistency, or the counting
    bound), SAT by an independently re-checked model."""
    # implication frame: a 2-SAT contradiction refutes the whole formula
    if not check_binary_clauses(formula).consistent:
        return FrameResult('UNSAT', '2sat', True, None)

    # parity frame, cheap side first: the sound GF(2) refutation is near-linear
    # (triangularize until a row hits 0 = 1). Measured ~30 ms at 4500 vars where
    # the full RREF solve below is ~1100 ms -- so refute before you reconstruct.
    if gf2_xor_refutation(formula).refuted:
        return FrameResult('UNSAT', 'parity', True, None)

    # parity frame, SAT side: pay the full GF(2) RREF only to *decide SAT* and
    # rebuild a model (which gf2_xor_solve re-verifies against the CNF inside).
    xr = gf2_xor_solve(formula)
    if xr.status == 'UNSAT':                      # defensive; refutation is primary
        return FrameResult('UNSAT', 'parity', True, None)
    if xr.status == 'SAT' and xr.model is not None and verify_model(formula, xr.model):
        return FrameResult('SAT', 'parity', True, dict(xr.model))

    # counting frame: the pigeonhole magnitude bound
    if pigeonhole_counting_refutation(formula).refuted:
        return FrameResult('UNSAT', 'counting', True, None)

    return FrameResult('CDCL_NEEDED', 'none', False, None)
