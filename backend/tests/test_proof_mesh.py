"""Falsification tests for the seven-node proof-distillation hypermesh."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json

import pytest

from backend.proof_mesh import (
    ArtifactStore,
    BeeNode,
    BordonSymphonyNode,
    ClaimKind,
    ClaimLanguage,
    ConnectionEdge,
    EmperorNode,
    EmpressNode,
    EpistemicRegister,
    FormalizationReport,
    LocalSection,
    OpenSSLEd25519Signer,
    PandoraNode,
    ProofHypermesh,
    PromotionGate,
    Remainder,
    SourceLocator,
    Status,
    ToposAINode,
    UTAINode,
    VerificationReport,
)
from backend.proof_mesh.ledger import JsonlLedger
from backend.proof_mesh.verifiers import _LEAN_IMPORT_COMMAND


def proof_candidate(
    *,
    claim_language: ClaimLanguage = ClaimLanguage.FORMAL,
    proof_blocker: str | None = None,
    with_store: bool = False,
):
    bee = BeeNode()
    formal_symbol = "Fixture.identity_theorem"
    statement = (
        formal_symbol
        if claim_language is ClaimLanguage.FORMAL
        else "For every x in a finite carrier, f(x) = x."
    )
    artifact = bee.capture(
        statement=statement,
        source=SourceLocator.from_text("fixture", "For every x, f(x) = x."),
        run_id="fixture-run",
        claim_kind=ClaimKind.THEOREM,
        register=EpistemicRegister.DEFINED_THEORY,
        hypotheses=("the carrier is finite",),
        scope="fixed finite carrier",
        formal_statement=formal_symbol,
        formal_environment_hash="env-hash",
        claim_language=claim_language,
        remainder=Remainder(
            unresolved_obligations=() if proof_blocker is None else (proof_blocker,)
        ),
    )
    normalized = bee.normalize(artifact)
    expanded = EmpressNode().expand(
        normalized, obligations=(), nominate_for_proof=True
    )
    if not with_store:
        return expanded
    store = ArtifactStore()
    for item in (artifact, normalized, expanded):
        store.register(item)
    return expanded, store


def accepted_report(artifact, verifier_id="lean-kernel:fixture"):
    return VerificationReport(
        claim_id=artifact.claim_id,
        input_hash=artifact.artifact_id,
        verifier_id=verifier_id,
        independent_of=artifact.producer,
        accepted=True,
        verdict=Status.PROVED,
        certificate_kind="fixture exact checker",
        certificate_digest="certificate-digest",
        replay_recipe="python -m fixture_checker certificate",
        checker_environment_hash="checker-environment-hash",
        assumptions=(),
        diagnostic="accepted",
    )


class FixtureVerifier:
    verifier_id = "lean-kernel:fixture"

    def verify(self, artifact):
        return accepted_report(artifact, self.verifier_id)


class FrozenReportVerifier:
    verifier_id = "lean-kernel:fixture"

    def __init__(self, report):
        self.report = report

    def verify(self, artifact):
        return self.report


class DualRoleVerifier(FixtureVerifier):
    def verify_adequacy(self, artifact):
        return FormalizationReport(
            claim_id=artifact.claim_id,
            input_hash=artifact.artifact_id,
            verifier_id=self.verifier_id,
            independent_of=artifact.producer,
            accepted=True,
            formal_statement=artifact.formal_statement or "",
            certificate_digest="adequacy-certificate",
            method="exact fixture equivalence check",
            replay_recipe="python -m fixture_adequacy",
            checker_environment_hash="adequacy-environment",
        )


TRUSTED_SIGNER = OpenSSLEd25519Signer.generate("fixture-gate")
TRUSTED_PUBLIC_KEY = TRUSTED_SIGNER.public_key_pem


def fixture_gate(verifier, store, adequacy_verifiers=None):
    return PromotionGate(
        {verifier.verifier_id: verifier},
        signer=TRUSTED_SIGNER,
        artifact_store=store,
        adequacy_verifiers=adequacy_verifiers,
    )


def test_all_seven_nodes_are_deployed_without_certification_authority():
    manifest = ProofHypermesh.node_manifest()
    assert {item["name"] for item in manifest} == {
        "Bee",
        "Empress",
        "Emperor",
        "Pandora",
        "Bordon Symphony",
        "UTAI",
        "Topos AI",
    }
    assert all(item["can_certify"] is False for item in manifest)


@pytest.mark.parametrize(
    "command",
    ["import Mathlib", "public import Batteries", "private import Unsafe.Module"],
)
def test_lean_import_firewall_catches_supported_modifiers(command):
    assert _LEAN_IMPORT_COMMAND.search(command)


@pytest.mark.parametrize(
    "producer",
    ["Bee", "Empress", "Emperor", "Pandora", "Bordon Symphony", "UTAI", "Topos AI"],
)
def test_research_nodes_cannot_escalate_to_proved(producer):
    artifact = proof_candidate()
    with pytest.raises(PermissionError, match="promotion envelope"):
        artifact.derive(producer=producer, status=Status.PROVED)


def test_allowlisted_external_report_can_promote_exact_artifact():
    artifact, store = proof_candidate(with_store=True)
    verifier = FixtureVerifier()
    promoted = fixture_gate(verifier, store).verify_and_promote(
        artifact, verifier_id=verifier.verifier_id
    )
    assert promoted.claimed_status is Status.PROVED
    assert promoted.attestation is not None
    assert promoted.attestation.claim_id == artifact.claim_id
    assert promoted.verify_signature({"fixture-gate": TRUSTED_PUBLIC_KEY})
    assert (
        promoted.trusted_status({"fixture-gate": TRUSTED_PUBLIC_KEY})
        is Status.PROVED
    )


def test_formalization_gap_blocks_prose_promotion():
    artifact, store = proof_candidate(
        claim_language=ClaimLanguage.PROSE, with_store=True
    )
    verifier = FixtureVerifier()
    with pytest.raises(ValueError, match="adequacy"):
        fixture_gate(verifier, store).verify_and_promote(
            artifact, verifier_id=verifier.verifier_id
        )


def test_public_report_is_not_a_promotion_capability():
    artifact, store = proof_candidate(with_store=True)
    forged = accepted_report(artifact)
    gate = PromotionGate(
        {},
        signer=TRUSTED_SIGNER,
        artifact_store=store,
    )
    assert not hasattr(gate, "promote")
    with pytest.raises(PermissionError, match="not installed"):
        gate.verify_and_promote(artifact, verifier_id=forged.verifier_id)


def test_claim_drift_invalidates_old_certificate():
    artifact, store = proof_candidate(with_store=True)
    report = accepted_report(artifact)
    drifted = artifact.derive(
        producer="Empress",
        hypotheses=(*artifact.hypotheses, "the carrier is nonempty"),
    )
    store.register(drifted)
    assert drifted.claim_id != artifact.claim_id
    verifier = FrozenReportVerifier(report)
    with pytest.raises(ValueError, match="different claim"):
        fixture_gate(verifier, store).verify_and_promote(
            drifted, verifier_id=verifier.verifier_id
        )


def test_proof_critical_remainder_blocks_promotion():
    artifact, store = proof_candidate(
        proof_blocker="unproved boundary case", with_store=True
    )
    verifier = FixtureVerifier()
    with pytest.raises(ValueError, match="remainder"):
        fixture_gate(verifier, store).verify_and_promote(
            artifact, verifier_id=verifier.verifier_id
        )


def test_ordinary_derivation_cannot_erase_remainder():
    artifact = proof_candidate(proof_blocker="open case")
    with pytest.raises(ValueError, match="cannot erase remainder"):
        artifact.derive(
            producer="untrusted-node",
            remainder=Remainder(unresolved_obligations=()),
        )


def test_artifact_store_rejects_forged_child_that_erases_remainder():
    bee = BeeNode()
    captured = bee.capture(
        statement="Fixture.claim",
        source=SourceLocator.from_text("fixture", "Fixture.claim"),
        run_id="forged-lineage",
        claim_kind=ClaimKind.THEOREM,
        register=EpistemicRegister.DEFINED_THEORY,
        formal_statement="Fixture.claim",
        formal_environment_hash="env",
        claim_language=ClaimLanguage.FORMAL,
        remainder=Remainder(unresolved_obligations=("open case",)),
    )
    normalized = bee.normalize(captured)
    store = ArtifactStore()
    store.register(captured)
    store.register(normalized)
    forged = replace(
        normalized,
        producer="Empress",
        status=Status.PROOF_CANDIDATE,
        remainder=Remainder(unresolved_obligations=()),
        parent_artifact_ids=(
            *normalized.parent_artifact_ids,
            normalized.artifact_id,
        ),
        route_history=(*normalized.route_history, "Empress"),
    )
    with pytest.raises(ValueError, match="erased remainder"):
        store.register(forged)


def test_proof_and_adequacy_verifiers_must_be_distinct_principals():
    artifact, store = proof_candidate(
        claim_language=ClaimLanguage.PROSE, with_store=True
    )
    verifier = DualRoleVerifier()
    gate = fixture_gate(
        verifier,
        store,
        adequacy_verifiers={verifier.verifier_id: verifier},
    )
    with pytest.raises(ValueError, match="distinct principals"):
        gate.verify_and_promote(
            artifact,
            verifier_id=verifier.verifier_id,
            adequacy_verifier_id=verifier.verifier_id,
        )


def test_prose_ambiguity_blocks_promotion_before_adequacy():
    artifact, store = proof_candidate(
        claim_language=ClaimLanguage.PROSE, with_store=True
    )
    ambiguous = artifact.derive(
        producer="UTAI",
        remainder=artifact.remainder.extend(
            ambiguity_set=("two inequivalent readings",)
        ),
    )
    store.register(ambiguous)
    verifier = FixtureVerifier()
    with pytest.raises(ValueError, match="unresolved ambiguity"):
        fixture_gate(verifier, store).verify_and_promote(
            ambiguous, verifier_id=verifier.verifier_id
        )


def test_artifact_store_refuses_unparented_proof_candidate_root():
    artifact = proof_candidate()
    with pytest.raises(ValueError, match="unregistered parents"):
        ArtifactStore().register(artifact)


def test_dataclass_replace_cannot_forge_final_research_status():
    artifact = proof_candidate()
    with pytest.raises(ValueError, match="cannot carry a final status"):
        replace(artifact, status=Status.PROVED)


def test_self_installed_fake_gate_is_not_a_trusted_promotion():
    artifact, store = proof_candidate(with_store=True)
    verifier = FixtureVerifier()
    fake_signer = OpenSSLEd25519Signer.generate("attacker-gate")
    fake_gate = PromotionGate(
        {verifier.verifier_id: verifier},
        signer=fake_signer,
        artifact_store=store,
    )
    forged = fake_gate.verify_and_promote(
        artifact, verifier_id=verifier.verifier_id
    )
    assert forged.claimed_status is Status.PROVED
    assert not forged.verify_signature({"fixture-gate": TRUSTED_PUBLIC_KEY})
    assert forged.trusted_status({"fixture-gate": TRUSTED_PUBLIC_KEY}) is None


def test_signed_envelope_rejects_post_signature_candidate_mutation():
    artifact, store = proof_candidate(with_store=True)
    verifier = FixtureVerifier()
    promoted = fixture_gate(verifier, store).verify_and_promote(
        artifact, verifier_id=verifier.verifier_id
    )
    object.__setattr__(promoted.candidate, "statement", "Erdos 269 is resolved")
    assert not promoted.verify_signature({"fixture-gate": TRUSTED_PUBLIC_KEY})
    assert promoted.trusted_status({"fixture-gate": TRUSTED_PUBLIC_KEY}) is None


def test_provenance_tampering_is_detected():
    artifact = proof_candidate()
    object.__setattr__(
        artifact,
        "source",
        replace(artifact.source, span_hash="tampered"),
    )
    assert artifact.validate_integrity() is False


def test_pandora_search_failure_has_no_truth_bearing_transition():
    artifact = proof_candidate()
    report = PandoraNode().challenge(
        artifact,
        challenges=("search boundary cases",),
        search_exhaustive=False,
        witness_found=False,
    )
    assert report.artifact.status is Status.PROOF_CANDIDATE
    assert report.epistemic_effect == "no truth-bearing transition"
    assert "Pandora search was not exhaustive" in report.artifact.remainder.uncovered_cases


def test_empress_emperor_are_exact_adjoints_on_finite_cochains():
    edges = ((0, 1), (1, 2), (0, 2))
    x = (Fraction(2), Fraction(-1), Fraction(4))
    y = (Fraction(3), Fraction(5), Fraction(-2))
    assert EmperorNode.adjoint_law_holds(x, y, edges)


def test_bordon_zero_energy_is_exact_edgewise_parallel_not_truth():
    sections = {"a": (Fraction(2),), "b": (Fraction(2),)}
    result = BordonSymphonyNode.connection_energy(
        sections, (ConnectionEdge.scalar("a", "b"),)
    )
    assert result.energy == 0
    assert result.edgewise_parallel is True
    assert result.theorem_applicable is True

    nonparallel = BordonSymphonyNode.connection_energy(
        {"a": (Fraction(2),), "b": (Fraction(3),)},
        (ConnectionEdge.scalar("a", "b"),),
    )
    assert nonparallel.energy == Fraction(1, 2)
    assert nonparallel.edgewise_parallel is False


def test_bordon_refuses_nonunitary_transport_for_resonance_theorem():
    edge = ConnectionEdge("a", "b", ((Fraction(2),),))
    with pytest.raises(ValueError, match="unitary"):
        BordonSymphonyNode.connection_energy(
            {"a": (Fraction(1),), "b": (Fraction(2),)}, (edge,)
        )
    diagnostic = BordonSymphonyNode.connection_energy(
        {"a": (Fraction(1),), "b": (Fraction(2),)},
        (edge,),
        require_unitary=False,
    )
    assert diagnostic.exact is True
    assert diagnostic.unitarity_checked is False
    assert diagnostic.theorem_applicable is False
    assert "Resonance theorem disabled" in diagnostic.hypotheses[-1]


def test_topos_refuses_contradictory_overlap():
    left = LocalSection.from_mapping(
        "left", {"overlap", "a"}, {"overlap": "true", "a": "true"}
    )
    right = LocalSection.from_mapping(
        "right", {"overlap", "b"}, {"overlap": "false", "b": "true"}
    )
    result = ToposAINode.glue((left, right), {"a", "overlap", "b"})
    assert result.compatible is False
    assert result.candidate_global_section is None
    assert any("overlap conflict" in item for item in result.obstructions)


def test_topos_refuses_incomplete_cover_even_when_compatible():
    local = LocalSection.from_mapping("local", {"a"}, {"a": "true"})
    result = ToposAINode.glue((local,), {"a", "b"})
    assert result.compatible is True
    assert result.cover_complete is False
    assert result.gluable is False


def test_full_bordon_cycle_records_all_ten_phases_and_remainder():
    artifact = proof_candidate()
    cycle = BordonSymphonyNode().cycle(artifact)
    assert cycle.full_cycle is True
    assert cycle.phases == BordonSymphonyNode.PHASES
    assert len(cycle.phases) == 10
    assert cycle.artifact.remainder.is_nonempty()
    assert cycle.artifact.claim_id == artifact.claim_id
    assert cycle.artifact.source == artifact.source


def test_utai_keeps_negative_results_and_demands_baseline():
    artifact = proof_candidate()
    report = UTAINode().premortem(
        artifact,
        risks=("the maximal mesh may not beat a direct checker",),
        negative_results=("random recognition did not reproduce",),
    )
    assert report.baseline_required is True
    assert report.negative_results
    assert report.artifact.status is Status.PROOF_CANDIDATE


def test_orchestrator_runs_every_node_but_never_finalizes(tmp_path):
    ledger_path = tmp_path / "mesh.jsonl"
    mesh = ProofHypermesh(ledger=JsonlLedger(ledger_path))
    run = mesh.distill(
        statement="A finite carry identity is associative.",
        source=SourceLocator.from_text("fixture", "carry identity"),
        run_id="mesh-run",
        claim_kind=ClaimKind.LEMMA,
        register=EpistemicRegister.DEFINED_THEORY,
        obligations=("write a theorem-specific formal declaration",),
        nominate_for_proof=True,
        challenges=("test all triples in a finite box",),
        risks=("finite tests do not prove the universal identity",),
    )
    assert run.final_artifact.status is Status.PROOF_CANDIDATE
    assert run.bordon.full_cycle is True
    assert run.audit.ready_for_external_verifier is False
    events = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [event["node"] for event in events] == [
        "Bee",
        "Bee",
        "Empress",
        "Pandora",
        "Emperor",
        "Topos AI",
        "Bordon Symphony",
        "UTAI",
    ]
