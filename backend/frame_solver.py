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
from .xor_extraction import (
    XORExtractionResult,
    _rref_gf2,
    extract_xors,
    gf2_xor_refutation,
    gf2_xor_solve,
)


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


# --------------------------------------------------------------------------
# The moving frame: a rotor that points the router at the LOCAL cheapest frame
# --------------------------------------------------------------------------
# frame_solve tries the frames in a FIXED order, so on the unstructured band it
# parses for XOR structure twice (gf2_xor_refutation and gf2_xor_solve each call
# extract_xors) only to find none, before giving up. The cosmo map
# (docs/ladder/scripts/cosmo_map.py) shows a formula's shallowest frame is a
# *frame field* over instance-space -- so instead of a fixed order, read the
# local structure once and rotate the trial order to it: parse ONE time, and
# skip the parity frame entirely when there is no parity structure to bite on.
# Verdicts are byte-identical to frame_solve (differential-tested); this only
# changes order and prunes provably-inapplicable frames.

def _parity_from_extracted(formula: CNFFormula, xr: XORExtractionResult,
                           n: int):
    """Decide the parity frame from an ALREADY-extracted XOR set (no re-parse):
    returns ('UNSAT'|'SAT'|'INCONCLUSIVE', model_or_None). Keeps frame_solve's
    refute-first shape -- cheap near-linear forward elimination for UNSAT, and
    the superlinear full RREF only to reconstruct a SAT model."""
    rows = []
    for x in xr.xors:
        row = 0
        for v in x.variables:
            row |= 1 << (v - 1)
        if x.rhs:
            row |= 1 << n
        rows.append(row)

    # cheap side first: forward-eliminate until a row collapses to 0 = 1 (this
    # is gf2_xor_refutation's near-linear core, run on the shared rows).
    pivots: Dict[int, int] = {}
    for r in rows:
        cur = r
        while cur:
            lead = (cur & -cur).bit_length() - 1
            if lead == n:                          # only the rhs bit left: 0 = 1
                return 'UNSAT', None
            if lead in pivots:
                cur ^= pivots[lead]
            else:
                pivots[lead] = cur
                break

    if xr.xor_clause_fraction < 0.999:             # consistent but parity ⊄ cover
        return 'INCONCLUSIVE', None
    basis = _rref_gf2(rows, n)                      # full RREF only for the model
    if basis is None:                              # defensive; already consistent
        return 'UNSAT', None
    model = {v: False for v in range(1, n + 1)}
    for pivot_col, row in basis.items():
        model[pivot_col + 1] = bool((row >> n) & 1)
    if verify_model(formula, model):               # verify, don't trust
        return 'SAT', model
    return 'INCONCLUSIVE', None


def frame_solve_guided(formula: CNFFormula) -> FrameResult:
    """Moving-frame router: same certified verdicts as `frame_solve`, but read
    the local structure once and rotate the trial order to it -- one shared
    parse, and skip the parity frame when the formula carries no XOR structure.
    Measured to roughly halve the pre-pass on the unstructured band (where the
    fixed-order router parses twice for a parity structure that is not there)."""
    if not check_binary_clauses(formula).consistent:
        return FrameResult('UNSAT', '2sat', True, None)

    xr = extract_xors(formula)                      # THE single parse (the rotor)
    n = formula.num_vars
    if xr.xors:                                     # parity structure present
        status, model = _parity_from_extracted(formula, xr, n)
        if status == 'UNSAT':
            return FrameResult('UNSAT', 'parity', True, None)
        if status == 'SAT':
            return FrameResult('SAT', 'parity', True, dict(model))

    if pigeonhole_counting_refutation(formula).refuted:
        return FrameResult('UNSAT', 'counting', True, None)

    return FrameResult('CDCL_NEEDED', 'none', False, None)
