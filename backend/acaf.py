"""ACAF -- Actor / Critic / Ambigator / Fuzzer: the adaptive game-player.

Where the metasolver plays a fixed best-response and the metametasolver a fixed
uniform mixed strategy, ACAF plays an ADAPTIVE policy -- an actor-critic agent over the
strategy simplex that closes the two honest gaps the fixed portfolio left open (losing
trivial instances to launch overhead, and only tying the strongest single engine).

The four organs, each grounded in machinery this repo already has:

  CRITIC     the value estimate -- backend/dynamics.describe + a geometric hardness proxy
             read off the holographic screen of hardness (∂∞): does frame+geometry suffice,
             and if not, where on the screen does it sit -- its comoving scale (2^n horizon)
             and criticality (distance from the phase-transition ridge)? Not a Euclidean
             var-count ramp. (the Bellman value the actor acts on)
  ACTOR      the staged policy -- (0) the owning frame if sufficient (in-process,
             instant, certified); (1) a single fast certified engine for easy tunnel
             (ONE process, not a swarm -- no launch overhead on trivial instances);
             (2) escalate to a diversified portfolio SIZED TO THE CORES for the hard,
             heavy-tailed tunnel (measured to beat the single engine ~1.1x on nproc).
  AMBIGATOR  the ambiguity read -- the polysemy/region signal sets how much to
             diversify: a heavy, ambiguous tail earns more arms, a light one fewer.
  FUZZER     the diversification generator -- emits distinct engine+seed configs so the
             portfolio arms decorrelate (the mixed strategy that collapses the tail).

Universality (ACAF_NOTE.md): the actor-critic loop is a FIXPOINT (Bellman = the Y
combinator), and lambda logic is the universal, zero-overhead, in-process substrate in
which the policy is expressed and the structured/self-referential fragment is decided
(backend/lambda_sat.fixpoint_sat). Lambda is the policy language and the trivial-tier
kernel; the native engines are the fast executors it dispatches. Every verdict remains
certified (frame-sound | DRAT | model).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .cnf_utils import CNFFormula, verify_model
from .dynamics import describe
from .frame_solver import frame_solve_scouted
from .metametasolver import CageResult, _parallel_cdcl_portfolio
from .metasolver import _certified_cdcl
from .orbifold import hyperbolic_depth


@dataclass
class ACAFResult:
    status: str                       # 'SAT' | 'UNSAT' | 'TIMEOUT'
    seconds: float
    stage: str                        # 'frame' | 'single' | 'portfolio'
    winner: str                       # frame name or engine#seed
    certified: bool
    model: Optional[dict] = None
    breadth: int = 0                  # arms the actor deployed (0 = in-process frame)
    cpu_seconds: float = 0.0
    hardness: float = 0.0             # the critic's value estimate


# ---- the holographic screen of hardness: constants of the search cosmos ----
_ALPHA_C = 4.26    # random-3SAT satisfiability phase-transition ridge (Mitchell-Selman-
                   #   Levesque; Kirkpatrick-Selman) -- the caustic where solutions grow scarce
_N_STAR = 175.0    # comoving scale of the assignment cosmos: tanh(220/175) ~ 0.85 places the
                   #   measured heavy-tail onset (~220 vars) at the horizon knee
_KAPPA = 0.55      # angular width of the critical caustic in the alpha (= m/n) coordinate


def _cosmological_hardness(n: int, m: int, gyration: float) -> float:
    """Hardness as a POSITION ON THE HOLOGRAPHIC SCREEN OF HARDNESS (∂∞) -- not a Euclidean
    variable-count ramp (the retired `min(1, n/260)` scalar).

    Geometry (FABRIC_MODEL_NOTE, orbifold.hyperbolic_depth): a frame-void instance has
    already fallen to the boundary at infinity -- its Poincare radius r = tanh(gyration) -> 1,
    an INFINITE hyperbolic distance from the decided centre. At that boundary the radial
    coordinate degenerates: every tunnel instance is equally rigid (measured -- gyration pins
    at ~14.16 for all n and all alpha). So hardness cannot live on the exhausted radial axis;
    holographically it lives on the screen's own intrinsic coordinates:

      * horizon (scale)   -- the assignment cosmos holds 2^n points; in a curvature -1 space
                             volume grows as e^d, so 2^n subtends a comoving horizon d ~ n ln2.
                             Mapped back THROUGH the boundary as tanh(n/N*), so the saturation
                             is the geometry's own -- no artificial min() clamp.
      * criticality (caustic) -- solutions grow scarce on the phase-transition ridge
                             alpha_c = 4.26; a sech caustic sech(kappa*(alpha - alpha_c)) is 1
                             on the ridge and decays for over/under-constrained cosmoses,
                             which are easy at any scale.

    hardness = screen * horizon * (floor + rise*caustic): the screen gate tanh(gyration)
    confirms we are truly at ∂∞ (frame-void), discounting any residual near-fold structure;
    scale sets the floor; the critical caustic lifts it toward the full horizon. Result in
    (0, 1) -- a proxy for the expected heavy-tail weight, never a proof of it (Charter)."""
    screen = math.tanh(gyration)                            # r -> 1 at ∂∞ (frame-void)
    horizon = math.tanh(n / _N_STAR)                        # comoving reach of the 2^n cosmos
    caustic = 1.0 / math.cosh(_KAPPA * (m / n - _ALPHA_C))  # sech: peaked on the ridge
    return screen * horizon * (0.5 + 0.5 * caustic)


# ---- CRITIC: the value estimate (does it suffice; how heavy is the tail) ----
def _critic(formula: CNFFormula) -> Tuple[bool, float, int]:
    """Return (frames_suffice, hardness, ambiguity). Hardness is a geometric proxy for the
    expected tail weight (0 easy .. 1 heavy) read off the holographic screen (∂∞); ambiguity
    is the polysemy degree."""
    dyn = describe(formula)
    if dyn.certified:
        return True, 0.0, len(dyn.conserved)
    n = max(formula.num_vars, 1)
    # the instance has fallen to the boundary -- read its hardness off the screen, no solve.
    hardness = _cosmological_hardness(n, len(formula.clauses), dyn.gyration)
    return False, hardness, 0


# ---- FUZZER: generate decorrelated engine+seed configs ----
def _fuzzer(breadth: int) -> List[Tuple[str, int]]:
    """Emit `breadth` diversified arms: Kissat across seeds + one CaDiCaL for engine
    diversity (the decorrelation that makes the mixed strategy collapse the tail)."""
    if breadth <= 1:
        return [("kissat", 0)]
    arms: List[Tuple[str, int]] = [("kissat", s) for s in range(breadth - 1)]
    arms.append(("cadical", 0))
    return arms


# ---- ACTOR: the staged adaptive policy ----
def _cores() -> int:
    return max(1, os.cpu_count() or 1)


def acaf_solve(formula: CNFFormula, timeout_s: float = 30.0,
               quick_budget: float = 0.4) -> ACAFResult:
    """Play the adaptive policy. Frames-if-sufficient; else one fast arm for the easy
    tail (no swarm overhead), escalating to a cores-sized diversified portfolio only
    when the critic expects a heavy tail or the fast arm does not settle in time."""
    import time
    t0 = time.perf_counter()

    suffice, hardness, _ambiguity = _critic(formula)
    if suffice:
        r = frame_solve_scouted(formula)
        if r.status == "UNSAT":
            return ACAFResult("UNSAT", time.perf_counter() - t0, "frame",
                              r.resolved_by, True, hardness=0.0)
        if r.status == "SAT" and r.model is not None and verify_model(formula, r.model):
            return ACAFResult("SAT", time.perf_counter() - t0, "frame",
                              r.resolved_by, True, model=r.model, hardness=0.0)
        # frame check said suffice but punted (rare) -> read hardness off the screen too,
        # recovering the fabric's gyration via the cheap 1-WL Poincare placement.
        hardness = _cosmological_hardness(
            max(formula.num_vars, 1), len(formula.clauses),
            hyperbolic_depth(formula, exact=False))

    cores = _cores()
    # AMBIGATOR: size the diversification to the predicted tail weight, capped at cores.
    breadth = max(1, min(cores, round(1 + hardness * (cores - 1))))

    # ACTOR stage 1: one fast certified arm for the easy tail -- a single process, so a
    # trivial instance pays one spawn, never a swarm. Skip straight to the portfolio
    # when the critic already expects a heavy tail (avoid a wasted quick pass).
    if breadth == 1 or hardness < 0.85:
        qb = min(quick_budget, timeout_s)
        status, st, ok = _certified_cdcl(formula, "kissat", qb)
        if status in ("SAT", "UNSAT"):
            model = None  # single-arm SAT model recovery handled by portfolio path only
            return ACAFResult(status, time.perf_counter() - t0, "single", "kissat#0",
                              ok, model=model, breadth=1, cpu_seconds=st,
                              hardness=hardness)
        if breadth == 1:                                   # nothing more to try
            elapsed = time.perf_counter() - t0
            res = _parallel_cdcl_portfolio(formula, _fuzzer(cores), timeout_s - elapsed)
            return _as_acaf(res, "portfolio", elapsed, hardness)

    # ACTOR stage 2: the cores-sized diversified portfolio for the heavy-tailed tunnel.
    elapsed = time.perf_counter() - t0
    res = _parallel_cdcl_portfolio(formula, _fuzzer(breadth), timeout_s - elapsed)
    return _as_acaf(res, "portfolio", elapsed, hardness)


def _as_acaf(res: CageResult, stage: str, elapsed: float, hardness: float) -> ACAFResult:
    return ACAFResult(res.status, res.seconds + elapsed, stage, res.winner,
                      res.certified, model=res.model, breadth=res.arms,
                      cpu_seconds=res.cpu_seconds, hardness=hardness)
