from src.hyperdim_protocol import (
    CORE_8_MIND_QUALITIES,
    CommunicationWindow,
    QUALITY_NAMES,
    communication_error,
    holoportation_loss,
    infer_state,
    noncollapsing_communication,
    nonflattening_score,
    plan_steps,
    projection_violence,
    run_protocol,
)
import pytest


def test_protocol_state_has_expected_hyperdimensional_basis():
    state = infer_state(
        evidence_quality=0.8,
        formal_frontier_clarity=0.75,
        mutual_recognition=0.9,
        resonance_gain=0.8,
        absorption_risk=0.1,
        sheaf_consistency=0.7,
        hamiltonian_governance=0.85,
        holoportation_fidelity=0.9,
        adiabatic_ratio=0.1,
        shareable_compression=0.8,
    )

    assert state.dimension == len(QUALITY_NAMES)
    assert len(CORE_8_MIND_QUALITIES) == 8
    assert state.core_8_score > 0.7
    assert state.split_signature_energy > 0.0
    assert state.stable


def test_protocol_prioritizes_grounding_when_returnability_is_weak():
    report = run_protocol(
        evidence_quality=0.5,
        formal_frontier_clarity=0.8,
        mutual_recognition=0.9,
        resonance_gain=0.95,
        absorption_risk=0.7,
        sheaf_consistency=0.8,
        hamiltonian_governance=0.75,
        holoportation_fidelity=0.8,
        adiabatic_ratio=0.2,
        shareable_compression=0.45,
    )

    top_names = {step.name for step in report.steps[:3]}

    assert report.needs_grounding
    assert "ground" in top_names
    assert 0.0 <= report.best_cognitive_performance <= 1.0


def test_holoportation_loss_detects_context_drift():
    source = infer_state(
        evidence_quality=0.9,
        formal_frontier_clarity=0.9,
        mutual_recognition=0.9,
        resonance_gain=0.9,
        absorption_risk=0.05,
        sheaf_consistency=0.9,
        hamiltonian_governance=0.9,
        holoportation_fidelity=0.9,
        adiabatic_ratio=0.05,
        shareable_compression=0.9,
    )
    target = infer_state(
        evidence_quality=0.3,
        formal_frontier_clarity=0.4,
        mutual_recognition=0.5,
        resonance_gain=0.6,
        absorption_risk=0.5,
        sheaf_consistency=0.4,
        hamiltonian_governance=0.35,
        holoportation_fidelity=0.4,
        adiabatic_ratio=0.8,
        shareable_compression=0.4,
    )

    assert holoportation_loss(source, source) == 0.0
    assert holoportation_loss(source, target) > 0.25


def test_plan_steps_orders_largest_deficit_first():
    state = infer_state(
        evidence_quality=0.8,
        formal_frontier_clarity=0.8,
        mutual_recognition=0.9,
        resonance_gain=0.9,
        absorption_risk=0.1,
        sheaf_consistency=0.2,
        hamiltonian_governance=0.9,
        holoportation_fidelity=0.9,
        adiabatic_ratio=0.05,
        shareable_compression=0.8,
    )

    steps = plan_steps(state)

    assert steps[0].name == "sheathe"


def test_nonflattening_requires_readability_and_active_remainder():
    assert nonflattening_score(1.0, 1.0) == 1.0
    assert nonflattening_score(1.0, 0.0) == 0.0
    assert nonflattening_score(0.0, 1.0) == 0.0
    assert nonflattening_score(0.7, 0.8) == 0.5599999999999999


def test_projection_nonflattening_is_part_of_state_basis():
    state = infer_state(
        evidence_quality=0.8,
        formal_frontier_clarity=0.75,
        mutual_recognition=0.9,
        resonance_gain=0.8,
        absorption_risk=0.1,
        sheaf_consistency=0.7,
        hamiltonian_governance=0.85,
        holoportation_fidelity=0.9,
        adiabatic_ratio=0.1,
        shareable_compression=0.8,
        projection_readability=0.9,
        active_remainder=0.7,
    )

    assert "projection_nonflattening" in QUALITY_NAMES
    assert state.score("projection_nonflattening") == 0.63


def test_projection_violence_weights_projection_losses():
    assert projection_violence(0.0, 0.0, 0.0, 0.0) == 0.0

    violent = projection_violence(
        reconstruction_loss=0.1,
        coherence_loss=0.2,
        curvature_loss=0.3,
        topology_loss=0.4,
        topology_weight=2.0,
    )

    assert violent == pytest.approx(1.4)


def test_noncollapsing_communication_requires_small_nonzero_error():
    pv = projection_violence(0.02, 0.03, 0.01, 0.02)
    error = communication_error(
        section_energy=0.08,
        algebra_defect=0.03,
        zero_divisor_shadow=0.01,
        holonomy_drift=0.02,
        curvature_mismatch=0.01,
        projection_violence_value=pv,
    )
    window = CommunicationWindow(
        upper_error=0.5,
        resonance_threshold=0.7,
        projection_violence_threshold=0.2,
        holonomy_drift_threshold=0.1,
        hamiltonian_drift_threshold=0.1,
    )

    assert noncollapsing_communication(
        error=error,
        resonance=0.9,
        projection_violence_value=pv,
        holonomy_drift=0.02,
        hamiltonian_drift=0.03,
        window=window,
    )
    assert not noncollapsing_communication(
        error=0.0,
        resonance=0.9,
        projection_violence_value=pv,
        holonomy_drift=0.02,
        hamiltonian_drift=0.03,
        window=window,
    )
    assert not noncollapsing_communication(
        error=0.9,
        resonance=0.9,
        projection_violence_value=pv,
        holonomy_drift=0.02,
        hamiltonian_drift=0.03,
        window=window,
    )
