"""lambda_bridge -- the Boolean lambda layer's CONTRIBUTION to the mesh.

Not equivalence -- contribution. A lambda term and its CNF projection are
equisatisfiable on the Boolean fragment, so "equivalence" would flatten lambda to
"just another way to write a CNF." That misses the point. The right question is
what lambda *contributes* that the flat frame/CNF view cannot express -- because
the qualities that drive cognitive and mathematical performance are generative
(composition, dynamics, metaphor, reframing), not mere sameness.

Lambda joins the mesh (it projects, so it gets a frame verdict and an orbifold
chart like any instance), and on top of that it contributes three things the CNF
snapshot does not carry:

  * COMPOSITION -- a term is built and reduced (beta), so it can be *assembled*
    from parts and *transformed* before it is a formula. The CNF is the rest
    state; the lambda term is the motion. (metaphor, load-bearing: reduction is
    where new structure is generated, e.g. a parity frame that only appears
    *after* beta-reduction -- test_lambda_sat.test_reduction_reveals_parity_frame.)
  * DYNAMICS (the epsilon>0 remainder) -- fixpoint_sat expresses a satisfiability
    MODE the flat frames structurally lack: a self-referential term (the Moebius
    lambda s. not s) never stabilizes, so its remainder is eternally active. No
    CNF frame can represent "satisfiable but never closed"; lambda contributes it.
  * ROUTING -- meta-resolution recognizes a frame in the term's normal form
    before projecting, so lambda can hand the right frame the right object.

`lambda_contribution` reports these axes; `lambda_signature` is the functor onto
the orbifold mesh. The projection is sound (decides => agrees with ground truth),
which is what lets the contribution be *trusted* rather than merely asserted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .cnf_utils import CNFFormula
from .frame_solver import FrameResult, frame_solve_coupled
from .lambda_sat import (
    App,
    BExpr,
    Lam,
    beta_normalize,
    eval_bool,
    fixpoint_sat,
    free_vars,
    tseitin_encode,
)
from .observer import ObserverVerdict, adjudicate
from .orbifold import SatSignature, satisfiability_signature


def project(term: BExpr) -> Tuple[CNFFormula, Dict[str, int]]:
    """The CNF shadow of a Boolean lambda term (beta-normalize, then Tseitin-
    encode, equisatisfiable). The functor's action on objects -- the same
    projection the frame router, observer and orbifold layers consume, so a
    lambda term becomes a first-class member of the mesh."""
    normal = beta_normalize(term)
    cnf, _remainder, free_ids = tseitin_encode(normal)
    return cnf, free_ids


def brute_truth(term: BExpr) -> str:
    """Ground-truth SAT/UNSAT of a term by enumerating its free variables."""
    from itertools import product
    normal = beta_normalize(term)
    fv = sorted(free_vars(normal))
    for bits in product([False, True], repeat=len(fv)):
        if eval_bool(normal, dict(zip(fv, bits))):
            return "SAT"
    return "UNSAT"


def frame_decide(term: BExpr) -> FrameResult:
    """Decide a lambda term through the coupled frame router on its projection."""
    cnf, _ = project(term)
    return frame_solve_coupled(cnf)


def observe(term: BExpr) -> ObserverVerdict:
    """Adjudicate a lambda term through the observer (accept/repair/escalate)."""
    cnf, _ = project(term)
    return adjudicate(cnf)


def lambda_signature(term: BExpr) -> SatSignature:
    """The orbifold satisfiability signature of a lambda term -- it acquires
    isotropy, polysemy, remainder and a hyperbolic depth, like any instance."""
    cnf, _ = project(term)
    return satisfiability_signature(cnf)


@dataclass
class Contribution:
    """What the lambda presentation ADDS over its flat CNF shadow."""
    equisatisfiable: bool     # the shared ground: projection preserves SAT/UNSAT
    adds_composition: bool    # the term has redexes/abstractions (motion, not rest)
    adds_dynamics: bool       # a fixpoint whose epsilon>0 remainder frames can't hold
    frame_after_reduction: str  # the frame that appears once reduced ('none' if -)


def _has_redex_or_abstraction(e: BExpr) -> bool:
    if isinstance(e, (Lam, App)):
        return True
    for attr in ("e", "l", "r", "fn", "arg", "body"):
        child = getattr(e, attr, None)
        if isinstance(child, BExpr) and _has_redex_or_abstraction(child):
            return True
    return False


def lambda_contribution(term: BExpr, fix_depth: int = 6) -> Contribution:
    """Report lambda's contribution over the CNF snapshot: whether it is
    equisatisfiable (the trusted shared ground), whether it carries composition
    and/or an active dynamic remainder, and which frame lambda's OWN meta-
    resolution surfaces (that routing is itself a contribution). Contribution,
    not equivalence -- these are the generative axes the flat view discards."""
    from .lambda_sat import lambda_sat
    adds_comp = _has_redex_or_abstraction(term)
    normal = beta_normalize(term)
    if isinstance(normal, Lam):
        # a bare abstraction has NO Boolean CNF shadow -- its whole contribution
        # is dynamic (the fixpoint remainder), exactly what the frames lack.
        try:
            adds_dyn = fixpoint_sat(normal, fix_depth).remainder_active
        except Exception:
            adds_dyn = False
        return Contribution(False, adds_comp, adds_dyn, "none")
    # Boolean normal form: lambda's meta-resolution picks the frame (its routing
    # sees parity in the term that the gate projection would bury).
    resolved_by = lambda_sat(term).resolved_by
    return Contribution(True, adds_comp, False, resolved_by)
