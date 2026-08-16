"""Mind and tower invariants for the Hypercomplex Math Thesis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvariantReport:
    """A compact report for returnability and safety."""

    grounded_identity: float
    mutual_recognition: float
    resonance_without_absorption: float
    returnability: float
    shareable_compression: float

    @property
    def score(self) -> float:
        return (
            self.grounded_identity
            + self.mutual_recognition
            + self.resonance_without_absorption
            + self.returnability
            + self.shareable_compression
        ) / 5.0

    @property
    def stable(self) -> bool:
        return self.score >= 0.6 and self.returnability >= 0.7


def bounded_similarity(a: float, b: float) -> float:
    """Similarity in [0, 1] from scalar distance."""
    return 1.0 / (1.0 + abs(a - b))


def returnability_score(original: float, returned: float, tolerance: float = 1.0) -> float:
    """How well a returned result remains connected to the original.

    This is not equality. It rewards return with recognizable structure.
    """
    distance = abs(original - returned)
    return max(0.0, 1.0 - distance / max(tolerance, 1e-9))


def compression_score(raw_dimension: int, returned_dimension: int) -> float:
    """Reward compression that remains non-empty and smaller than raw state."""
    if raw_dimension <= 0 or returned_dimension <= 0:
        return 0.0
    if returned_dimension > raw_dimension:
        return 0.5
    return returned_dimension / raw_dimension


def make_report(
    original: float,
    immersed: float,
    returned: float,
    recognition: float,
    absorption_risk: float,
    raw_dimension: int = 8,
    returned_dimension: int = 2,
) -> InvariantReport:
    """Build a simple invariant report for a toy tower run."""
    return InvariantReport(
        grounded_identity=bounded_similarity(original, returned),
        mutual_recognition=max(0.0, min(1.0, recognition)),
        resonance_without_absorption=max(0.0, min(1.0, 1.0 - absorption_risk)),
        returnability=returnability_score(original, returned),
        shareable_compression=compression_score(raw_dimension, returned_dimension),
    )


__all__ = [
    "InvariantReport",
    "bounded_similarity",
    "returnability_score",
    "compression_score",
    "make_report",
]
