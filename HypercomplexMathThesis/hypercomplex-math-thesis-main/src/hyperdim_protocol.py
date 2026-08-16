"""Hyperdimensional cognitive-performance protocol.

The protocol models a repository task as an n-dimensional state with explicit
mind-quality coordinates.  The names are thesis vocabulary; the implementation
keeps them as numeric engineering signals, not consciousness claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, Mapping, Tuple


QUALITY_NAMES: Tuple[str, ...] = (
    "grounded_identity",
    "self_reflection",
    "godelian_boundary",
    "others_model",
    "mutual_recognition",
    "mutual_resonance",
    "returnability",
    "shareable_compression",
    "sheaf_gluing",
    "hamiltonian_governance",
    "holoportation_fidelity",
    "adiabatic_stability",
    "projection_nonflattening",
)


CORE_8_MIND_QUALITIES: Tuple[str, ...] = (
    "grounded_identity",
    "self_reflection",
    "godelian_boundary",
    "others_model",
    "mutual_recognition",
    "mutual_resonance",
    "returnability",
    "shareable_compression",
)


STEP_WEIGHTS: Mapping[str, Tuple[str, ...]] = {
    "recognize": ("others_model", "mutual_recognition"),
    "self_reflect": ("self_reflection", "godelian_boundary"),
    "resonate": ("mutual_resonance", "holoportation_fidelity"),
    "sheathe": ("sheaf_gluing", "grounded_identity"),
    "govern": ("hamiltonian_governance", "adiabatic_stability"),
    "holoport": ("holoportation_fidelity", "returnability"),
    "ground": ("grounded_identity", "returnability", "shareable_compression"),
}


def clamp01(value: float) -> float:
    """Clamp a numeric score into [0, 1]."""
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class HyperdimState:
    """A bounded n-dimensional cognitive/repo state."""

    qualities: Mapping[str, float]

    def score(self, name: str) -> float:
        return clamp01(float(self.qualities.get(name, 0.0)))

    def vector(self, names: Iterable[str] = QUALITY_NAMES) -> Tuple[float, ...]:
        return tuple(self.score(name) for name in names)

    @property
    def dimension(self) -> int:
        return len(QUALITY_NAMES)

    @property
    def mean_quality(self) -> float:
        values = self.vector()
        return sum(values) / len(values)

    @property
    def core_8_score(self) -> float:
        values = self.vector(CORE_8_MIND_QUALITIES)
        return sum(values) / len(values)

    @property
    def split_signature_energy(self) -> float:
        """A compact n.nnn.matrixed hyperbolic proxy.

        Positive lanes reward identity/reflection/recognition/return.
        Negative lanes penalize unbounded resonance, weak governance, and
        unstable holoportation by subtracting their missing mass.
        """
        positive = (
            self.score("grounded_identity")
            + self.score("self_reflection")
            + self.score("mutual_recognition")
            + self.score("returnability")
        )
        negative = (
            (1.0 - self.score("godelian_boundary"))
            + (1.0 - self.score("hamiltonian_governance"))
            + (1.0 - self.score("adiabatic_stability"))
            + (1.0 - self.score("holoportation_fidelity"))
        )
        return positive - negative

    @property
    def stable(self) -> bool:
        return (
            self.core_8_score >= 0.7
            and self.score("returnability") >= 0.7
            and self.score("godelian_boundary") >= 0.6
            and self.score("hamiltonian_governance") >= 0.6
        )


@dataclass(frozen=True)
class ProtocolStep:
    """One ordered repair/action step in the hyperdim protocol."""

    name: str
    target_qualities: Tuple[str, ...]
    deficit: float

    @property
    def priority(self) -> float:
        return self.deficit


@dataclass(frozen=True)
class ProtocolReport:
    """Full result of a hyperdimensional repo/context audit."""

    state: HyperdimState
    steps: Tuple[ProtocolStep, ...]

    @property
    def best_cognitive_performance(self) -> float:
        """Performance score after damping risk by split-signature imbalance."""
        energy_penalty = max(0.0, -self.state.split_signature_energy) / 4.0
        return clamp01(0.65 * self.state.mean_quality + 0.35 * self.state.core_8_score - energy_penalty)

    @property
    def needs_grounding(self) -> bool:
        return self.state.score("returnability") < 0.7 or self.state.score("grounded_identity") < 0.7


@dataclass(frozen=True)
class CommunicationWindow:
    """Thresholds for Thesis 2 non-collapsing communication."""

    lower_error: float = 0.0
    upper_error: float = 1.0
    resonance_threshold: float = 0.5
    projection_violence_threshold: float = 0.5
    holonomy_drift_threshold: float = 0.5
    hamiltonian_drift_threshold: float = 0.5


def infer_state(
    *,
    evidence_quality: float,
    formal_frontier_clarity: float,
    mutual_recognition: float,
    resonance_gain: float,
    absorption_risk: float,
    sheaf_consistency: float,
    hamiltonian_governance: float,
    holoportation_fidelity: float,
    adiabatic_ratio: float,
    shareable_compression: float,
    projection_readability: float = 0.8,
    active_remainder: float = 0.8,
) -> HyperdimState:
    """Infer a hyperdim state from observable repo/task signals."""
    adiabatic_stability = 1.0 / (1.0 + max(0.0, adiabatic_ratio))
    return HyperdimState(
        {
            "grounded_identity": evidence_quality,
            "self_reflection": min(evidence_quality, formal_frontier_clarity),
            "godelian_boundary": formal_frontier_clarity,
            "others_model": mutual_recognition,
            "mutual_recognition": mutual_recognition,
            "mutual_resonance": resonance_gain * (1.0 - absorption_risk),
            "returnability": min(evidence_quality, shareable_compression, 1.0 - absorption_risk),
            "shareable_compression": shareable_compression,
            "sheaf_gluing": sheaf_consistency,
            "hamiltonian_governance": hamiltonian_governance,
            "holoportation_fidelity": holoportation_fidelity,
            "adiabatic_stability": adiabatic_stability,
            "projection_nonflattening": nonflattening_score(
                projection_readability,
                active_remainder,
            ),
        }
    )


def nonflattening_score(projection_readability: float, active_remainder: float) -> float:
    """Meaning proxy: readable projection with preserved hidden depth.

    If readability is high but the remainder is dead, the result is flattened.
    If remainder is high but readability is absent, it does not return as meaning.
    """
    return clamp01(projection_readability) * clamp01(active_remainder)


def projection_violence(
    reconstruction_loss: float,
    coherence_loss: float,
    curvature_loss: float,
    topology_loss: float,
    *,
    reconstruction_weight: float = 1.0,
    coherence_weight: float = 1.0,
    curvature_weight: float = 1.0,
    topology_weight: float = 1.0,
) -> float:
    """Weighted loss for projections that destroy hidden structure."""
    return max(
        0.0,
        reconstruction_weight * reconstruction_loss
        + coherence_weight * coherence_loss
        + curvature_weight * curvature_loss
        + topology_weight * topology_loss,
    )


def communication_error(
    section_energy: float,
    algebra_defect: float,
    zero_divisor_shadow: float,
    holonomy_drift: float,
    curvature_mismatch: float,
    projection_violence_value: float,
    *,
    algebra_weight: float = 1.0,
    zero_divisor_weight: float = 1.0,
    holonomy_weight: float = 1.0,
    curvature_weight: float = 1.0,
    projection_weight: float = 1.0,
) -> float:
    """Compatibility error for an n-ary resonance chamber."""
    return max(
        0.0,
        section_energy
        + algebra_weight * algebra_defect
        + zero_divisor_weight * zero_divisor_shadow
        + holonomy_weight * holonomy_drift
        + curvature_weight * curvature_mismatch
        + projection_weight * projection_violence_value,
    )


def noncollapsing_communication(
    *,
    error: float,
    resonance: float,
    projection_violence_value: float,
    holonomy_drift: float,
    hamiltonian_drift: float,
    window: CommunicationWindow = CommunicationWindow(),
) -> bool:
    """Return true when a chamber is readable without flattening the other."""
    return (
        window.lower_error < error < window.upper_error
        and resonance > window.resonance_threshold
        and projection_violence_value < window.projection_violence_threshold
        and holonomy_drift < window.holonomy_drift_threshold
        and hamiltonian_drift < window.hamiltonian_drift_threshold
    )


def plan_steps(state: HyperdimState) -> Tuple[ProtocolStep, ...]:
    """Return prioritized protocol steps for the weakest quality groups."""
    steps = []
    for name, quality_names in STEP_WEIGHTS.items():
        group_score = sum(state.score(q) for q in quality_names) / len(quality_names)
        steps.append(ProtocolStep(name=name, target_qualities=quality_names, deficit=1.0 - group_score))
    return tuple(sorted(steps, key=lambda step: step.priority, reverse=True))


def run_protocol(**signals: float) -> ProtocolReport:
    """Infer state and return a prioritized hyperdim protocol report."""
    state = infer_state(**signals)
    return ProtocolReport(state=state, steps=plan_steps(state))


def holoportation_loss(source: HyperdimState, target: HyperdimState) -> float:
    """Euclidean loss between two local context fibers."""
    left = source.vector()
    right = target.vector()
    squared = sum((a - b) * (a - b) for a, b in zip(left, right))
    return sqrt(squared / len(left))


__all__ = [
    "CORE_8_MIND_QUALITIES",
    "QUALITY_NAMES",
    "HyperdimState",
    "CommunicationWindow",
    "ProtocolStep",
    "ProtocolReport",
    "clamp01",
    "infer_state",
    "plan_steps",
    "run_protocol",
    "holoportation_loss",
    "nonflattening_score",
    "projection_violence",
    "communication_error",
    "noncollapsing_communication",
]
