"""Adiabatic breathing toy model.

The model is intentionally small: a state moves under a Hamiltonian-like swirl
while curvature and grounding pressure breathe slowly.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from typing import Iterable, List, Tuple


Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class BreathParams:
    """Parameters for a breathing manifold toy model."""

    curvature_base: float = -1.0
    curvature_amp: float = 0.25
    breath_rate: float = 0.05
    hamiltonian_rate: float = 1.0
    grounding: float = 0.05

    def curvature(self, t: float) -> float:
        return self.curvature_base + self.curvature_amp * sin(self.breath_rate * t)


@dataclass(frozen=True)
class BreathState:
    """A point and its current time."""

    x: float
    y: float
    t: float = 0.0

    @property
    def radius2(self) -> float:
        return self.x * self.x + self.y * self.y


def hamiltonian_swirl(state: BreathState, params: BreathParams) -> Vector2:
    """A simple rotational vector field modulated by curvature."""
    k = abs(params.curvature(state.t))
    omega = params.hamiltonian_rate * (1.0 + 0.5 * k)
    return (-omega * state.y, omega * state.x)


def grounding_pull(state: BreathState, params: BreathParams) -> Vector2:
    """A weak pull toward the origin representing returnability/grounding."""
    return (-params.grounding * state.x, -params.grounding * state.y)


def step(state: BreathState, params: BreathParams, dt: float = 0.01) -> BreathState:
    """Advance the breathing toy model by one Euler step."""
    vx, vy = hamiltonian_swirl(state, params)
    gx, gy = grounding_pull(state, params)
    return BreathState(
        x=state.x + dt * (vx + gx),
        y=state.y + dt * (vy + gy),
        t=state.t + dt,
    )


def simulate(
    initial: BreathState,
    params: BreathParams,
    steps: int = 1000,
    dt: float = 0.01,
) -> List[BreathState]:
    """Simulate a trajectory."""
    states = [initial]
    current = initial
    for _ in range(steps):
        current = step(current, params, dt=dt)
        states.append(current)
    return states


def adiabaticity_ratio(params: BreathParams) -> float:
    """Toy ratio: breath rate divided by Hamiltonian rate.

    Smaller is more adiabatic.
    """
    return abs(params.breath_rate) / max(abs(params.hamiltonian_rate), 1e-9)


def is_adiabatic(params: BreathParams, threshold: float = 0.1) -> bool:
    return adiabaticity_ratio(params) <= threshold


__all__ = [
    "BreathParams",
    "BreathState",
    "hamiltonian_swirl",
    "grounding_pull",
    "step",
    "simulate",
    "adiabaticity_ratio",
    "is_adiabatic",
]
