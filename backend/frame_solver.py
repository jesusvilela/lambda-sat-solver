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


# --------------------------------------------------------------------------
# The coupled triple: three frames as three theories, exchanging entailed
# literals over shared variables (Nelson-Oppen combination) to a fixpoint
# --------------------------------------------------------------------------
# Each frame decides its own theory; the "spin coupling" is the shared variable.
# A literal one frame *entails* propagates as a fact into the other two, shrinking
# them, which entails more -- iterate. This decides instances NO single frame
# decides alone (e.g. a parity system SAT on its own + 2-SAT units SAT on their
# own, jointly UNSAT once the units are substituted into the parity rows). It runs
# ONLY when frame_solve punts, so it is a strict extension at bounded extra cost.

@dataclass
class CoupledResult:
    status: str                       # 'SAT' | 'UNSAT' | 'CDCL_NEEDED'
    resolved_by: str                  # a single frame, or 'coupled', or 'none'
    certified: bool
    model: Optional[Dict[int, bool]]
    rounds: int                       # propagation rounds to fixpoint
    forced: int                       # variables pinned by cross-frame exchange


def _bcp(clauses_le2, fixed: Dict[int, bool]):
    """Unit-propagate the <=2-literal clauses under `fixed` to its own fixpoint,
    mutating `fixed` with entailed literals. Returns (ok, changed); ok=False is a
    sound implication-frame conflict."""
    changed = False
    again = True
    while again:
        again = False
        for c in clauses_le2:
            sat = False
            unassigned = []
            for lit in c:
                v = abs(lit)
                if v in fixed:
                    if fixed[v] == (lit > 0):
                        sat = True
                        break
                else:
                    unassigned.append(lit)
            if sat:
                continue
            if not unassigned:
                return False, changed              # every literal false: conflict
            if len(unassigned) == 1:
                lit = unassigned[0]
                fixed[abs(lit)] = (lit > 0)
                changed = again = True
    return True, changed


def _parity_propagate(xor_rows, n: int, fixed: Dict[int, bool]):
    """Substitute `fixed` into the XOR rows and Gaussian-eliminate. Returns
    'CONFLICT' (sound parity inconsistency) or a dict of newly ENTAILED literals
    (variables pinned to a constant by a weight-1 reduced row)."""
    rhs_bit = 1 << n
    var_mask = rhs_bit - 1
    basis: Dict[int, int] = {}
    for row in xor_rows:
        cur = row
        for v, b in fixed.items():                 # substitute fixed variables
            m = 1 << (v - 1)
            if cur & m:
                cur ^= m
                if b:
                    cur ^= rhs_bit
        while cur & var_mask:                       # reduce against the basis
            low = cur & var_mask
            lead = (low & -low).bit_length() - 1
            if lead in basis:
                cur ^= basis[lead]
            else:
                basis[lead] = cur
                break
        if not (cur & var_mask) and cur == rhs_bit:
            return 'CONFLICT'                        # 0 = 1
    forced: Dict[int, bool] = {}
    for row in basis.values():
        vbits = row & var_mask
        if vbits and (vbits & (vbits - 1)) == 0:     # exactly one variable left
            forced[vbits.bit_length()] = bool(row & rhs_bit)
    return forced


def _simplify(formula: CNFFormula, fixed: Dict[int, bool]) -> CNFFormula:
    """Apply `fixed`: drop satisfied clauses, remove falsified literals."""
    out = []
    for c in formula.clauses:
        nc = []
        sat = False
        for lit in c:
            v = abs(lit)
            if v in fixed:
                if fixed[v] == (lit > 0):
                    sat = True
                    break
            else:
                nc.append(lit)
        if not sat:
            out.append(nc)
    return CNFFormula(num_vars=formula.num_vars, clauses=out)


def frame_solve_coupled(formula: CNFFormula, max_rounds: int = 64) -> CoupledResult:
    """Couple the three frames: run the pure single-frame router first, and only
    if it punts, exchange entailed literals across the frames to a fixpoint. Sound
    by construction -- every emitted literal is entailed (2-SAT unit propagation,
    a weight-1 GF(2) row), every UNSAT is a channel refutation, and SAT is only
    ever returned with an independently verified model."""
    base = frame_solve(formula)
    if base.status != 'CDCL_NEEDED':                # a single frame already decides
        return CoupledResult(base.status, base.resolved_by, base.certified,
                             base.model, 0, 0)

    n = formula.num_vars
    le2 = [c for c in formula.clauses if len(c) <= 2]
    xr = extract_xors(formula)
    xor_rows = []
    for x in xr.xors:
        row = 0
        for v in x.variables:
            row |= 1 << (v - 1)
        if x.rhs:
            row |= 1 << n
        xor_rows.append(row)

    fixed: Dict[int, bool] = {}
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        ok, bcp_changed = _bcp(le2, fixed)
        if not ok:
            return CoupledResult('UNSAT', 'coupled', True, None, rounds, len(fixed))
        pres = _parity_propagate(xor_rows, n, fixed)
        if pres == 'CONFLICT':
            return CoupledResult('UNSAT', 'coupled', True, None, rounds, len(fixed))
        parity_changed = False
        for v, b in pres.items():
            if v not in fixed:
                fixed[v] = b
                parity_changed = True
        simp = _simplify(formula, fixed)
        if any(len(c) == 0 for c in simp.clauses):   # a wide clause fully falsified
            return CoupledResult('UNSAT', 'coupled', True, None, rounds, len(fixed))
        if pigeonhole_counting_refutation(simp).refuted:
            return CoupledResult('UNSAT', 'coupled', True, None, rounds, len(fixed))
        if not (bcp_changed or parity_changed):      # fixpoint
            break

    model = {v: fixed.get(v, False) for v in range(1, n + 1)}
    if verify_model(formula, model):                 # sound completion attempt
        return CoupledResult('SAT', 'coupled', True, model, rounds, len(fixed))
    return CoupledResult('CDCL_NEEDED', 'none', False, None, rounds, len(fixed))


# --------------------------------------------------------------------------
# Structure-gated router: read a cheap tunnel signal first and skip the frame
# pre-pass on instances with no exploitable algebraic structure. On unstructured
# random-3SAT the coupled router otherwise parses for XOR/counting structure that
# is not there (2-3 wasted extract passes + a coupling loop) before punting to CDCL.
#
# The gate is a LIGHT structural probe, not the full scout: measured, the scout's
# symmetry_partition (1-WL) costs MORE than the pre-pass it would save (net 0.28x
# on random-3SAT), whereas one XOR extract + a cheap ALO/AMO scan gates the same
# tunnel at ~3.3x speedup. The Charter way: the cheaper detector wins, measured.
# --------------------------------------------------------------------------
def _no_exploitable_structure(formula: CNFFormula, xr: XORExtractionResult) -> bool:
    """Cheap sufficient condition for TUNNEL: no XOR groups AND no pigeonhole-shaped
    counting structure (an all-positive ALO clause together with a negative-binary
    AMO clause). When both are absent, neither the parity nor the counting frame can
    bite, and with the 2-SAT frame already consistent the coupling cannot either --
    so the coupled router would punt to CDCL anyway, only after wasted work."""
    if xr.xors:
        return False
    has_alo = any(c and all(l > 0 for l in c) for c in formula.clauses)
    has_amo = any(len(c) == 2 and c[0] < 0 and c[1] < 0 for c in formula.clauses)
    return not (has_alo and has_amo)


def frame_solve_scouted(formula: CNFFormula, use_scout: bool = True) -> CoupledResult:
    """Structure-gated coupled router. Same certified SAT/UNSAT verdicts as
    `frame_solve_coupled`, but on a cheap TUNNEL signal (no XOR and no counting
    structure) it skips the algebraic pre-pass and reports CDCL_NEEDED immediately
    -- removing the wasted parity/coupling work on structureless instances
    (measured ~3.3x faster on random-3SAT).

    Soundness: the gate only ever short-circuits the CDCL_NEEDED *punt* (which
    frame_solve_coupled also returns on these instances, just after more work); it
    never turns a frame SAT/UNSAT into a punt. The 2-SAT frame (near-free, sound) is
    always taken first, and any XOR- or counting-shaped instance fails the gate and
    gets the full coupling. Differential-tested against frame_solve_coupled
    (0 verdict mismatches, 0 frame-wins lost) in tests/test_frame_solver.py."""
    if not check_binary_clauses(formula).consistent:
        return CoupledResult('UNSAT', '2sat', True, None, 0, 0)
    if use_scout and _no_exploitable_structure(formula, extract_xors(formula)):
        return CoupledResult('CDCL_NEEDED', 'none', False, None, 0, 0)
    return frame_solve_coupled(formula)


# --------------------------------------------------------------------------
# The bordon made dynamical: the coupling BREATHES (propagates round by round)
# and RESONATES (settles to a fixpoint). The one sustained tone -- a remainder
# that never settles, epsilon>0 -- lives in the self-referential lambda layer
# (lambda_sat.fixpoint_sat, the Moebius drone), not in any finite CNF, whose
# coupling is monotone and always resonates to rest.
# --------------------------------------------------------------------------
@dataclass
class BreathTrace:
    breath: list                      # |fixed| after each coupling round (inhale)
    rounds: int
    amplitude: int                    # deepest single-round intake
    settled: bool                     # reached a fixpoint/conflict (resonant rest)
    verdict: str                      # 'SAT' | 'UNSAT' | 'CDCL_NEEDED'
    entailed: Dict[int, bool] = None  # the literals the coupling ENTAILED (sound)


def coupling_breath(formula: CNFFormula, max_rounds: int = 64) -> BreathTrace:
    """Instrument the coupled router as a dynamical system: record the breath
    (the count of entailed literals after each propagation round -- the inhale)
    and whether it settles to a fixpoint (resonance to rest). A single frame that
    decides immediately is a 0-round rest; an instance that needs several rounds
    of cross-frame exchange breathes visibly before settling."""
    base = frame_solve(formula)
    if base.status != 'CDCL_NEEDED':
        return BreathTrace([], 0, 0, True, base.status, {})

    n = formula.num_vars
    le2 = [c for c in formula.clauses if len(c) <= 2]
    xr = extract_xors(formula)
    xor_rows = []
    for x in xr.xors:
        row = 0
        for v in x.variables:
            row |= 1 << (v - 1)
        if x.rhs:
            row |= 1 << n
        xor_rows.append(row)

    fixed: Dict[int, bool] = {}
    breath: list = []
    rounds = 0
    verdict = 'CDCL_NEEDED'
    settled = False
    while rounds < max_rounds:
        rounds += 1
        ok, bcp_changed = _bcp(le2, fixed)
        if not ok:
            breath.append(len(fixed))
            verdict, settled = 'UNSAT', True
            break
        pres = _parity_propagate(xor_rows, n, fixed)
        if pres == 'CONFLICT':
            breath.append(len(fixed))
            verdict, settled = 'UNSAT', True
            break
        parity_changed = False
        for v, b in pres.items():
            if v not in fixed:
                fixed[v] = b
                parity_changed = True
        breath.append(len(fixed))
        simp = _simplify(formula, fixed)
        if any(len(c) == 0 for c in simp.clauses) or \
                pigeonhole_counting_refutation(simp).refuted:
            verdict, settled = 'UNSAT', True
            break
        if not (bcp_changed or parity_changed):
            settled = True
            break

    if verdict == 'CDCL_NEEDED':
        model = {v: fixed.get(v, False) for v in range(1, n + 1)}
        if verify_model(formula, model):
            verdict = 'SAT'
    amplitude = max((breath[i] - (breath[i - 1] if i else 0)
                     for i in range(len(breath))), default=0)
    return BreathTrace(breath, rounds, amplitude, settled, verdict, dict(fixed))


def coupled_entailments(formula: CNFFormula):
    """The sound literals the coupling ENTAILS, even when it does not fully decide
    -- GRD's escape field made concrete: carry the accumulated moving-frame
    structure into the CDCL fallback instead of discarding it. Returns
    (entailed: {var: bool}, verdict). Every entailed literal is implied by the
    formula (2-SAT unit / weight-1 GF(2) row), so appending them as units is
    satisfiability-preserving -- a sound warm-start."""
    bt = coupling_breath(formula)
    return (bt.entailed or {}), bt.verdict
