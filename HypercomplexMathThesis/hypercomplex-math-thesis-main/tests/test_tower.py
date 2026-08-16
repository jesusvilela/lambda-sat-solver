from src.hypercomplex_breathing import BreathParams, BreathState, is_adiabatic, simulate
from src.invariants import make_report, returnability_score
from src.operators import convex_resonate, make_scalar_tower


def test_scalar_tower_returns_grounded_value():
    tower = make_scalar_tower()

    assert tower.solve(3.0, symmetry=2.0) == 6.0


def test_resonance_tracks_absorption_risk():
    result = convex_resonate(0.0, 10.0, coupling=0.25)

    assert result.left == 1.25
    assert result.right == 8.75
    assert 0.0 <= result.recognition <= 1.0
    assert 0.0 <= result.absorption_risk <= 1.0
    assert result.safe


def test_returnability_and_report_stability_are_explicit():
    assert returnability_score(1.0, 1.1, tolerance=1.0) > 0.8

    report = make_report(
        original=1.0,
        immersed=1.0,
        returned=1.1,
        recognition=0.9,
        absorption_risk=0.1,
        raw_dimension=8,
        returned_dimension=2,
    )

    assert report.returnability > 0.8
    assert report.score > 0.6


def test_breathing_model_keeps_adiabatic_ratio_visible():
    params = BreathParams(breath_rate=0.05, hamiltonian_rate=1.0)
    states = simulate(BreathState(0.5, 0.0), params, steps=10, dt=0.01)

    assert len(states) == 11
    assert is_adiabatic(params)
    assert states[-1].t > states[0].t
