"""scout -- the omni viscosity medium as a predictive field over instance-space.

Instead of one solving stream, treat the whole space as filled with GRD's
viscosity medium and SCOUT it: from cheap algebraic *detectors* (far cheaper than
the *deciders* they forecast), predict where an instance sits relative to the
decidability fold -- on the ISLAND (a frame will decide it), in TUNNEL territory
(no structure, straight to CDCL), or in the FOLD boundary layer (partial
structure, genuinely ambiguous -- run the coupling to find out).

Honest finding baked in (ESCAPE_FIELD_NOTE.md): the *decision* is a sharp
catastrophe fold, but the *predictive field* is smooth enough to scout, EXCEPT in
a boundary layer at partial coverage where whether the coupling decides depends on
the exact GF(2) rank, not a cheap feature. And structure is invisible to
clause-shape (Tseitin and random look identical by clause length) -- you must run
the algebraic detectors (xor recovery, symmetry refinement) to sense the medium.

Payoff: on confident TUNNEL the scout lets the router skip the frame deciders and
go straight to certified CDCL, removing the pre-pass overhead on unstructured
instances; on confident ISLAND it names the frame; only the FOLD band pays for the
full coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .binary_clause_check import check_binary_clauses
from .cardinality_check import pigeonhole_counting_refutation
from .cnf_utils import CNFFormula
from .orbifold import symmetry_partition
from .xor_extraction import extract_xors

ISLAND = "island"       # a sound frame will decide it
TUNNEL = "tunnel"       # no exploitable structure -> straight to CDCL
FOLD = "fold"           # partial structure -> boundary layer, ambiguous


@dataclass
class ScoutReport:
    region: str                       # ISLAND | TUNNEL | FOLD
    predicted_frame: str              # '2sat' | 'parity' | 'counting' | 'none'
    confidence: float                 # 0..1, from how deep in the region
    features: Dict[str, float]


def scout_features(formula: CNFFormula) -> Dict[str, float]:
    """Cheap detectors -- the medium's sensors. All poly and cheaper than the
    Gaussian/coupling/CDCL deciders they forecast."""
    n = max(formula.num_vars, 1)
    m = max(len(formula.clauses), 1)
    xor = extract_xors(formula).xor_clause_fraction
    part = symmetry_partition(formula)
    return {
        "xor": xor,
        "binary": sum(1 for c in formula.clauses if len(c) == 2) / m,
        "amo": sum(1 for c in formula.clauses
                   if len(c) == 2 and all(l < 0 for l in c)) / m,
        "symmetry": 1.0 - len(part) / n,       # 0 rigid ... ->1 highly symmetric
        "ratio": m / n,
    }


def scout(formula: CNFFormula) -> ScoutReport:
    """Predict the instance's region relative to the decidability fold, from the
    cheap detectors -- the viscosity medium scouted, not the trajectory run."""
    f = scout_features(formula)
    # a 2-SAT contradiction is cheap to confirm and always on the island
    if not check_binary_clauses(formula).consistent:
        return ScoutReport(ISLAND, "2sat", 1.0, f)
    # full parity coverage: the GF(2) decider almost always fires
    if f["xor"] >= 0.999:
        return ScoutReport(ISLAND, "parity", 1.0, f)
    # counting signature: symmetric + at-most-one heavy (PHP-like)
    if f["symmetry"] >= 0.6 and f["amo"] >= 0.2 or \
            pigeonhole_counting_refutation(formula).refuted:
        return ScoutReport(ISLAND, "counting", 0.9, f)
    # partial parity: the fold boundary layer -- ambiguous, must run the coupling
    if f["xor"] >= 0.25:
        return ScoutReport(FOLD, "none", 1.0 - f["xor"], f)
    # no exploitable structure: tunnel territory, straight to CDCL
    conf = 1.0 - max(f["xor"], f["amo"], f["symmetry"] if f["symmetry"] > 0 else 0.0)
    return ScoutReport(TUNNEL, "none", conf, f)
