"""Local deployment of the seven-node proof-distillation hypermesh."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Mapping, Sequence

from .artifacts import (
    ClaimKind,
    ClaimLanguage,
    EpistemicRegister,
    ProofArtifact,
    Remainder,
    SourceLocator,
)
from .ledger import JsonlLedger, LedgerEvent
from .nodes import (
    AuditReport,
    BeeNode,
    BordonCycleResult,
    BordonSymphonyNode,
    ChallengeReport,
    ConnectionEdge,
    EmperorNode,
    EmpressNode,
    GluingResult,
    LocalSection,
    PandoraNode,
    PremortemReport,
    ToposAINode,
    UTAINode,
)


@dataclass(frozen=True)
class MeshRun:
    run_id: str
    artifacts: tuple[ProofArtifact, ...]
    challenge: ChallengeReport
    audit: AuditReport
    gluing: GluingResult | None
    bordon: BordonCycleResult
    premortem: PremortemReport

    @property
    def final_artifact(self) -> ProofArtifact:
        return self.artifacts[-1]

    def to_dict(self) -> dict[str, Any]:
        def fraction_payload(value: Fraction) -> dict[str, int]:
            return {"numerator": value.numerator, "denominator": value.denominator}

        energy = self.bordon.energy
        return {
            "run_id": self.run_id,
            "final_artifact": self.final_artifact.to_dict(),
            "route": [artifact.producer for artifact in self.artifacts],
            "statuses": [artifact.status.value for artifact in self.artifacts],
            "challenge": {
                "challenges": self.challenge.challenges,
                "search_exhaustive": self.challenge.search_exhaustive,
                "witness_found": self.challenge.witness_found,
                "epistemic_effect": self.challenge.epistemic_effect,
            },
            "audit": {
                "integrity_ok": self.audit.integrity_ok,
                "ready_for_external_verifier": self.audit.ready_for_external_verifier,
                "blockers": self.audit.blockers,
            },
            "gluing": None
            if self.gluing is None
            else {
                "compatible": self.gluing.compatible,
                "cover_complete": self.gluing.cover_complete,
                "gluable": self.gluing.gluable,
                "obstructions": self.gluing.obstructions,
            },
            "bordon": {
                "full_cycle": self.bordon.full_cycle,
                "phases": self.bordon.phases,
                "energy": None
                if energy is None
                else fraction_payload(energy.energy),
                "edgewise_parallel": None
                if energy is None
                else energy.edgewise_parallel,
                "theorem_applicable": None
                if energy is None
                else energy.theorem_applicable,
            },
            "premortem": {
                "risks": self.premortem.risks,
                "negative_results": self.premortem.negative_results,
                "baseline_required": self.premortem.baseline_required,
            },
        }


class ProofHypermesh:
    """A proof-firewalled seven-node local mesh.

    The orchestrator never owns a ``PromotionGate``. That separation is
    deliberate: a research run cannot accidentally certify itself.
    """

    def __init__(self, ledger: JsonlLedger | None = None):
        self.bee = BeeNode()
        self.empress = EmpressNode()
        self.emperor = EmperorNode()
        self.pandora = PandoraNode()
        self.bordon = BordonSymphonyNode()
        self.utai = UTAINode()
        self.topos = ToposAINode()
        self.ledger = ledger

    @classmethod
    def node_manifest(cls) -> tuple[dict[str, Any], ...]:
        contracts = (
            BeeNode.contract,
            EmpressNode.contract,
            EmperorNode.contract,
            PandoraNode.contract,
            BordonSymphonyNode.contract,
            UTAINode.contract,
            ToposAINode.contract,
        )
        return tuple(
            {
                "name": contract.name,
                "operator": contract.operator,
                "metric": contract.metric,
                "may_emit": tuple(status.value for status in contract.may_emit),
                "prohibition": contract.prohibition,
                "can_certify": False,
            }
            for contract in contracts
        )

    def _record(
        self,
        artifacts: list[ProofArtifact],
        artifact: ProofArtifact,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        artifacts.append(artifact)
        if self.ledger is None:
            return
        self.ledger.append(
            LedgerEvent(
                run_id=artifact.run_id,
                sequence=len(artifacts),
                event_type=event_type,
                node=artifact.producer,
                artifact_id=artifact.artifact_id,
                claim_id=artifact.claim_id,
                status=artifact.status.value,
                payload=payload or {},
            )
        )

    def distill(
        self,
        *,
        statement: str,
        source: SourceLocator,
        run_id: str,
        claim_kind: ClaimKind = ClaimKind.CONJECTURE,
        register: EpistemicRegister = EpistemicRegister.INTERPRETIVE_CONJECTURAL,
        hypotheses: Iterable[str] = (),
        scope: str = "",
        formal_statement: str | None = None,
        formal_environment_hash: str | None = None,
        claim_language: ClaimLanguage = ClaimLanguage.PROSE,
        initial_remainder: Remainder | None = None,
        constraints: Iterable[str] = (),
        obligations: Iterable[str] = (),
        nominate_for_proof: bool = False,
        challenges: Iterable[str] = (),
        search_exhaustive: bool = False,
        witness_found: bool = False,
        local_sections: Sequence[LocalSection] = (),
        declared_domain: Iterable[str] = (),
        fiber_sections: Mapping[str, Sequence[int | Fraction]] | None = None,
        connection_edges: Sequence[ConnectionEdge] = (),
        risks: Iterable[str] = (),
        negative_results: Iterable[str] = (),
    ) -> MeshRun:
        artifacts: list[ProofArtifact] = []
        declared_domain_tuple = tuple(declared_domain)

        captured = self.bee.capture(
            statement=statement,
            source=source,
            run_id=run_id,
            claim_kind=claim_kind,
            register=register,
            hypotheses=hypotheses,
            scope=scope,
            formal_statement=formal_statement,
            formal_environment_hash=formal_environment_hash,
            claim_language=claim_language,
            remainder=initial_remainder,
            constraints=constraints,
        )
        self._record(artifacts, captured, "captured")

        normalized = self.bee.normalize(captured)
        self._record(artifacts, normalized, "normalized")

        expanded = self.empress.expand(
            normalized,
            obligations=obligations,
            nominate_for_proof=nominate_for_proof,
        )
        self._record(artifacts, expanded, "extended")

        challenge = self.pandora.challenge(
            expanded,
            challenges=challenges,
            search_exhaustive=search_exhaustive,
            witness_found=witness_found,
        )
        self._record(
            artifacts,
            challenge.artifact,
            "challenged",
            {"epistemic_effect": challenge.epistemic_effect},
        )

        audit = self.emperor.audit(challenge.artifact)
        self._record(
            artifacts,
            audit.artifact,
            "audited",
            {"ready_for_external_verifier": audit.ready_for_external_verifier},
        )

        gluing = (
            self.topos.glue(local_sections, declared_domain_tuple)
            if local_sections or declared_domain_tuple
            else None
        )
        descent_review = self.topos.review_artifact(audit.artifact, gluing)
        self._record(
            artifacts,
            descent_review,
            "descent_review",
            {
                "gluable": None if gluing is None else gluing.gluable,
                "obstructions": () if gluing is None else gluing.obstructions,
            },
        )
        energy = (
            self.bordon.connection_energy(fiber_sections, connection_edges)
            if fiber_sections is not None
            else None
        )
        cycle = self.bordon.cycle(descent_review, energy=energy, gluing=gluing)
        self._record(
            artifacts,
            cycle.artifact,
            "bordon_cycle",
            {"full_cycle": cycle.full_cycle},
        )

        premortem = self.utai.premortem(
            cycle.artifact,
            risks=risks,
            negative_results=negative_results,
        )
        self._record(artifacts, premortem.artifact, "premortem")

        return MeshRun(
            run_id=run_id,
            artifacts=tuple(artifacts),
            challenge=challenge,
            audit=audit,
            gluing=gluing,
            bordon=cycle,
            premortem=premortem,
        )
