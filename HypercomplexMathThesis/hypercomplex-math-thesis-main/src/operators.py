"""Operator grammar for the Hypercomplex Math Thesis.

This module keeps the first implementation deliberately small and inspectable.
It is not a claim that the full thesis is implemented; it is a typed scaffold
for experimentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Tuple, TypeVar

P = TypeVar("P")
I = TypeVar("I")
L = TypeVar("L")
S = TypeVar("S")
G = TypeVar("G")


@dataclass(frozen=True)
class TowerOperator(Generic[P, I, L, S, G]):
    """Immersion -> lift -> rotation -> ground.

    The tower is safe only when the final ground step is defined.
    """

    immerse: Callable[[P], I]
    lift: Callable[[I], L]
    rotate: Callable[[G, L], L]
    ground: Callable[[L], S]

    def solve(self, problem: P, symmetry: G) -> S:
        """Return a grounded solution from a problem and symmetry element."""
        inside = self.immerse(problem)
        lifted = self.lift(inside)
        rotated = self.rotate(symmetry, lifted)
        return self.ground(rotated)


@dataclass(frozen=True)
class ResonanceResult(Generic[L]):
    """Result of resonance between two lifted states."""

    left: L
    right: L
    recognition: float
    absorption_risk: float

    @property
    def safe(self) -> bool:
        """A conservative safety predicate."""
        return self.recognition > 0.05 and self.absorption_risk < 0.8


def convex_resonate(left: float, right: float, coupling: float) -> ResonanceResult[float]:
    """Toy scalar resonance preserving distinction when coupling < 1.

    coupling = 0 means no resonance.
    coupling = 1 collapses both states to their midpoint.
    """
    if not 0.0 <= coupling <= 1.0:
        raise ValueError("coupling must lie in [0, 1]")

    midpoint = 0.5 * (left + right)
    new_left = (1.0 - coupling) * left + coupling * midpoint
    new_right = (1.0 - coupling) * right + coupling * midpoint
    distance_before = abs(left - right)
    distance_after = abs(new_left - new_right)

    recognition = 1.0 / (1.0 + distance_before)
    absorption_risk = 1.0 - (distance_after / distance_before) if distance_before else 1.0
    return ResonanceResult(new_left, new_right, recognition, absorption_risk)


def identity_ground(x: L) -> L:
    """Trivial grounding used in tests and toy examples."""
    return x


def make_scalar_tower() -> TowerOperator[float, float, float, float, float]:
    """A minimal tower over scalar states.

    - immerse: treat the scalar as the lived problem
    - lift: embed by doubling precision/scale
    - rotate: multiply by a symmetry scalar
    - ground: compress back by half
    """

    return TowerOperator(
        immerse=lambda p: p,
        lift=lambda i: 2.0 * i,
        rotate=lambda g, l: g * l,
        ground=lambda l: 0.5 * l,
    )


__all__ = [
    "TowerOperator",
    "ResonanceResult",
    "convex_resonate",
    "identity_ground",
    "make_scalar_tower",
]
