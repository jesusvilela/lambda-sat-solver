"""
Rule-based heuristic/budget selection from a CNF profile.

Deliberately simple (explicit if/else rules, not learned) so its behavior
is auditable and its effect on solve time can be validated against plain
Kissat before any more sophisticated (learned) policy replaces it.
"""

from __future__ import annotations

from .cnf_profile import CNFProfile
from .kissat_wrapper import Budget, Heuristic

#: Names matching the configs benchmarked earlier against this repo's
#: instance set (pigeonhole + random 3-SAT): "aggressive" (decay=30,
#: vivify) had the lowest PAR-2 average there, "conservative" (plain
#: VSIDS) was close behind with less variance. Until there's benchmark
#: evidence for a case where a different config wins, this policy only
#: chooses between those two.
CONSERVATIVE = Heuristic(
    branching='vsids', restarts='geometric', phase='saved', vivify=False
)
AGGRESSIVE = Heuristic(
    branching='lrb', restarts='luby', phase='false', vivify=True
)


def choose_heuristic(profile: CNFProfile) -> Heuristic:
    """Pick a heuristic configuration from structural features.

    An earlier version of this rule routed high-Horn-ratio formulas to
    CONSERVATIVE on the theory that they're "cheap regardless, so skip
    vivify's overhead." Checked against this repo's own 13-instance
    benchmark (4 pigeonhole + 9 random 3-SAT), that rule was wrong:
    AGGRESSIVE won on all 4 pigeonhole instances (horn_ratio 0.97-0.98),
    including a 2x margin on the hardest one (91.9s vs 191.2s). Across
    all 13 instances AGGRESSIVE won or tied 10/13, with the 3 losses all
    on trivial sub-100ms instances where the difference is noise.

    So: no feature in `profile` has yet demonstrated it predicts a case
    where CONSERVATIVE should be preferred. Until a broader, more diverse
    benchmark (e.g. SATLIB-scale, multiple problem families) produces
    real counter-evidence, AGGRESSIVE is simply the better default here,
    and this function doesn't yet do per-instance selection - it's a
    placeholder for when there's evidence to justify branching on
    `profile` at all.
    """
    del profile  # no feature has shown predictive value yet; see docstring
    return AGGRESSIVE


def choose_budget(
    profile: CNFProfile,
    time_limit: int = 60,
    memory_limit: int = 2048,
) -> Budget:
    """Pick a resource budget for a formula.

    Currently a fixed budget regardless of profile - a hook point for
    size-scaled budgets once there's benchmark evidence to justify a
    specific scaling rule.
    """
    del profile  # unused for now; kept in the signature for future scaling
    return Budget(time_limit=time_limit, memory_limit=memory_limit)
