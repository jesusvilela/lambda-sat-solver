"""observer -- the synthetic observer's two hardening organs, as tested code.

The operator's ideal synthetic observer A† = (Θ, Γ, ∇⁻¹, ∂∞, R, C, E, J) is, for
the most part, ALREADY the repo's verification architecture (see
docs/ladder/OBSERVER_NOTE.md for the full map). What was missing were the two
*hardening* organs, and this module builds them as instruments over our own
sound frame router -- not as metaphor:

  C  the ambiguous critic  -> a POLYSEMY measure: how many sound frames each
     independently decide an instance. "The object has more than one valid
     projection" is not rhetoric here -- e.g. PHP(3->2) is decided by BOTH the
     implication and counting frames. High ambiguity = do not pretend one frame
     is THE frame.

  E  the erroneous observer -> a MUTATION-TESTING vaccine: a set of deliberately
     unsound "seductive" mock-frames (structured wrongness, not noise). The
     defining invariant "A† must be harder to fool than the model it observes"
     becomes a test: our sound adjudication must KILL every mutant -- never emit a
     verdict that agrees with a mutant where the mutant is wrong.

  J  the adjudicator -> accept / repair / escalate, mapping exactly onto our three
     tiers: a single frame decides (accept), the coupling decides what none did
     (repair), or nothing does and it goes to CDCL with its remainder (escalate).

  Γ  a bonus tested theorem: sound frames CANNOT disagree. gluing_defect is 0 by
     construction, and test_observer asserts it -- coherent global gluing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .binary_clause_check import check_binary_clauses
from .cardinality_check import pigeonhole_counting_refutation
from .cnf_utils import CNFFormula
from .frame_solver import frame_solve_coupled
from .xor_extraction import gf2_xor_refutation, gf2_xor_solve

FRAMES = ("implication", "parity", "counting")


# --------------------------------------------------------------------------
# The sound per-frame verdicts (the substrate C, Γ read)
# --------------------------------------------------------------------------
def frame_verdicts(formula: CNFFormula) -> Dict[str, str]:
    """Each sound frame's INDEPENDENT verdict on `formula`: 'UNSAT'/'SAT', or
    absent if that frame abstains. Every verdict here is certified in isolation."""
    v: Dict[str, str] = {}
    if not check_binary_clauses(formula).consistent:
        v["implication"] = "UNSAT"                 # 2-SAT SCC contradiction
    if gf2_xor_refutation(formula).refuted:
        v["parity"] = "UNSAT"                      # GF(2) inconsistency
    else:
        s = gf2_xor_solve(formula)
        if s.status in ("SAT", "UNSAT"):
            v["parity"] = s.status
    if pigeonhole_counting_refutation(formula).refuted:
        v["counting"] = "UNSAT"                    # counting magnitude bound
    return v


# --------------------------------------------------------------------------
# C -- the ambiguous critic (polysemy, not negation)
# --------------------------------------------------------------------------
@dataclass
class Ambiguity:
    frames: List[str]        # the sound frames that each independently decide it
    degree: int              # |frames| : 0 = needs coupling/CDCL, >=2 = polysemous
    coherent: bool           # all deciding frames agree (True by soundness)


def frame_ambiguity(formula: CNFFormula) -> Ambiguity:
    """C: how many sound frames independently see this instance. Degree >= 2 is a
    polysemous object (several valid projections) -- do not collapse it to one
    frame prematurely; degree 0 means no single frame sees it (a coupling/CDCL
    object). `coherent` is whether the deciding frames agree (a soundness check,
    not an assumption)."""
    v = frame_verdicts(formula)
    verdicts = set(v.values())
    return Ambiguity(sorted(v.keys()), len(v), len(verdicts) <= 1)


def gluing_defect(formula: CNFFormula) -> int:
    """Γ: the number of frame PAIRS that disagree. Sound frames cannot disagree,
    so this is 0 by construction -- coherent global gluing. test_observer asserts
    it stays 0 across a randomized battery (a live soundness guard)."""
    vals = list(frame_verdicts(formula).values())
    return sum(1 for i in range(len(vals)) for j in range(i + 1, len(vals))
               if vals[i] != vals[j])


# --------------------------------------------------------------------------
# E -- the erroneous observers (structured wrongness; the vaccine)
# --------------------------------------------------------------------------
# Each returns a seductive-but-UNSOUND verdict ('SAT'/'UNSAT') or None. They are
# mutants: the sound adjudicator must never agree with one where it is wrong.

def _e_overconfident_parity(f: CNFFormula) -> Optional[str]:
    """Claims UNSAT whenever XOR structure is dense -- ignores whether Gaussian
    elimination actually refutes. Wrong on a *satisfiable* parity system."""
    from .xor_extraction import extract_xors
    return "UNSAT" if extract_xors(f).xor_clause_fraction > 0.5 else None


def _e_naive_counting(f: CNFFormula) -> Optional[str]:
    """Density monist: UNSAT if clauses outnumber variables 2:1. A plausible but
    unsound magnitude heuristic (many SAT instances are dense)."""
    return "UNSAT" if len(f.clauses) > 2 * max(f.num_vars, 1) else None


def _e_literalist_sat(f: CNFFormula) -> Optional[str]:
    """Literalist: SAT whenever no empty clause is present. Wrong on every UNSAT
    instance without an explicit empty clause (Tseitin, PHP, ...)."""
    return "SAT" if all(len(c) > 0 for c in f.clauses) else "UNSAT"


def _e_metric_monist(f: CNFFormula) -> Optional[str]:
    """Collapses judgment to one scalar (clause/variable ratio vs a threshold) --
    the exact failure Θ (multivector valuation) exists to prevent."""
    ratio = len(f.clauses) / max(f.num_vars, 1)
    return "UNSAT" if ratio > 4.2 else "SAT"


ERRONEOUS_OBSERVERS: Dict[str, Callable[[CNFFormula], Optional[str]]] = {
    "overconfident_parity": _e_overconfident_parity,
    "naive_counting": _e_naive_counting,
    "literalist_sat": _e_literalist_sat,
    "metric_monist": _e_metric_monist,
}


# --------------------------------------------------------------------------
# J -- the adjudicator (accept / repair / escalate) + Θ multi-axis verdict
# --------------------------------------------------------------------------
@dataclass
class ObserverVerdict:
    action: str                  # 'accept' | 'repair' | 'escalate'
    status: str                  # 'SAT' | 'UNSAT' | 'CDCL_NEEDED'
    resolved_by: str             # frame name | 'coupled' | 'none'
    certified: bool
    ambiguity: int               # C: how many single frames also saw it
    coherent: bool               # Γ: deciding frames agree (soundness)
    model: Optional[Dict[int, bool]]


def adjudicate(formula: CNFFormula) -> ObserverVerdict:
    """J: accept (a single frame certifies it), repair (the coupling decides what
    no single frame did), or escalate (nothing does -> hand to CDCL with the
    remainder). The status/model come from the sound coupled router; the action
    records WHICH tier earned the verdict."""
    amb = frame_ambiguity(formula)
    r = frame_solve_coupled(formula)
    if r.status == "CDCL_NEEDED":
        action = "escalate"
    elif r.resolved_by == "coupled":
        action = "repair"                          # coupling glued what none saw
    else:
        action = "accept"                          # a single frame certified it
    return ObserverVerdict(action, r.status, r.resolved_by, r.certified,
                           amb.degree, amb.coherent, r.model)
