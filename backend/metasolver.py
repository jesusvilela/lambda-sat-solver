"""metasolver -- revert the dynamical description into a dispatch that beats every
individual solver, including CryptoMiniSat.

The operator's arc: float outside, collect the laws/relations/motions of the solve
(backend/dynamics.describe), then REVERT that description into operation -- use its
descriptive power precisely where the concrete frames and geometry do not suffice.

The dispatch:

  * `describe` reads whether frame + geometry SUFFICE (a certified verdict with no
    search). When they do -- the counting and parity islands -- the metasolver
    returns that certified verdict in ~0 ms. This is where it strictly beats CMS:
    CMS is exponential on the counting fragment (measured: php10/php12 time out while
    the counting frame refutes in ~0 ms), and ties on parity.
  * Where they do NOT suffice -- the unstructured tunnel -- the description hands off
    to a DRAT-certified CDCL engine on the ORIGINAL formula. Honest scope (measured,
    BEAT_CMS_NOTE.md): on pure random-3SAT the metasolver does not out-CDCL CMS; it
    MATCHES the strong CDCL engines there. The aggregate win over CMS comes from the
    structured axis and the description that routes to it, not from out-searching CMS
    on the tail.

Every verdict is certified: a frame UNSAT is a sound channel refutation, a frame SAT
is a re-verified model, and the CDCL fallback is DRAT-checked (UNSAT) or model-replay
checked (SAT). The metasolver never trusts CMS for a verdict; CMS is only a
competitor in the benchmark.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .cnf_utils import CNFFormula, verify_model, write_dimacs
from .dynamics import Dynamics, describe
from .frame_solver import frame_solve_scouted
from .proof_checking import DRATChecker


@dataclass
class MetaResult:
    status: str                       # 'SAT' | 'UNSAT' | 'TIMEOUT'
    seconds: float
    strategy: str                     # '2sat'|'parity'|'counting'|'coupled'|<engine>
    certified: bool                   # verdict is certified (frame-sound | DRAT | model)
    model: Optional[Dict[int, bool]] = None
    dynamics: Optional[Dynamics] = None


_ENGINE_CMD = {
    "kissat": lambda cnf, proof: ["kissat", "--relaxed", str(cnf), str(proof)],
    "cadical": lambda cnf, proof: ["cadical", str(cnf), str(proof)],
}


def _certified_cdcl(formula: CNFFormula, engine: str, timeout_s: float):
    """Run a CDCL engine on the ORIGINAL formula and certify: UNSAT by drat-trim,
    SAT by model replay. Returns (status, seconds, verified)."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        cnfp, proofp = d / "f.cnf", d / "f.drat"
        write_dimacs(formula, cnfp)
        t0 = time.perf_counter()
        try:
            p = subprocess.run(_ENGINE_CMD[engine](cnfp, proofp),
                               capture_output=True, text=True,
                               timeout=max(1.0, timeout_s))
        except subprocess.TimeoutExpired:
            return "TIMEOUT", float(timeout_s), False
        dt = time.perf_counter() - t0
        if p.returncode == 20:                                   # UNSAT
            res = DRATChecker().check_proof(formula, proofp, timeout=60)
            return "UNSAT", time.perf_counter() - t0, res.valid
        if p.returncode == 10:                                   # SAT
            model = {}
            for line in p.stdout.splitlines():
                if line.startswith("v "):
                    for tok in line[2:].split():
                        lit = int(tok)
                        if lit != 0:
                            model[abs(lit)] = (lit > 0)
            return "SAT", dt, verify_model(formula, model)
        return "TIMEOUT", dt, False


def _select_engine(dyn: Dynamics) -> str:
    """Description-driven CDCL choice for the tunnel. Measured (BEAT_CMS_NOTE.md):
    Kissat and CaDiCaL split wins on random-3SAT with no cheap feature reliably
    predicting the winner, so we default to Kissat (the strongest single engine) and
    keep description-driven engine-selection an honest open lens rather than a
    shipped predictor. The hook stays here so the dispatch is explicit."""
    return "kissat"


def metasolve(formula: CNFFormula, timeout_s: float = 20.0) -> MetaResult:
    """Dispatch by the dynamical description. Frame/geometry-sufficient instances are
    decided by a certified frame in ~0 ms (the CMS-beating axis); the rest hand off
    to a DRAT-certified CDCL engine on the original formula."""
    t0 = time.perf_counter()

    # LAWS/RELATIONS suffice? -> certified frame verdict, no search.
    r = frame_solve_scouted(formula)
    if r.status == "UNSAT":
        return MetaResult("UNSAT", time.perf_counter() - t0, r.resolved_by, True)
    if r.status == "SAT" and r.model is not None and verify_model(formula, r.model):
        return MetaResult("SAT", time.perf_counter() - t0, r.resolved_by, True,
                          model=r.model)

    # frame + geometry do NOT suffice: revert the description into a dispatch.
    dyn = describe(formula)
    engine = _select_engine(dyn)
    elapsed = time.perf_counter() - t0
    status, ct, verified = _certified_cdcl(formula, engine, timeout_s - elapsed)
    return MetaResult(status, elapsed + ct, engine, verified, dynamics=dyn)
