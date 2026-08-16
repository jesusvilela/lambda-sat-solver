"""The seven untrusted research nodes.

Every node has an operator, an output metric, and an explicit prohibition.
None receives the capability needed to construct a final proof artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from typing import Iterable, Mapping, Sequence

from .artifacts import (
    ClaimKind,
    ClaimLanguage,
    EpistemicRegister,
    Evidence,
    EvidenceKind,
    ProofArtifact,
    Remainder,
    SourceLocator,
    Status,
    canonical_json,
)


Scalar = Fraction
Vector = tuple[Scalar, ...]
Matrix = tuple[tuple[Scalar, ...], ...]


def _fraction(value: int | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _inner(left: Sequence[Scalar], right: Sequence[Scalar]) -> Scalar:
    if len(left) != len(right):
        raise ValueError("inner product dimension mismatch")
    return sum((a * b for a, b in zip(left, right)), Fraction(0))


def _transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return ()
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("ragged matrix")
    return tuple(tuple(matrix[i][j] for i in range(len(matrix))) for j in range(width))


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("matrix/vector dimension mismatch")
    return tuple(_inner(row, vector) for row in matrix)


def _matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right:
        raise ValueError("empty matrices are not transports")
    right_t = _transpose(right)
    if len(left[0]) != len(right):
        raise ValueError("matrix multiplication dimension mismatch")
    return tuple(tuple(_inner(row, col) for col in right_t) for row in left)


def _identity(dimension: int) -> Matrix:
    return tuple(
        tuple(Fraction(int(i == j)) for j in range(dimension))
        for i in range(dimension)
    )


def _is_orthogonal(matrix: Matrix) -> bool:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        return False
    return _matmul(_transpose(matrix), matrix) == _identity(len(matrix))


@dataclass(frozen=True)
class NodeContract:
    name: str
    operator: str
    metric: str
    may_emit: tuple[Status, ...]
    prohibition: str


@dataclass(frozen=True)
class AuditReport:
    artifact: ProofArtifact
    integrity_ok: bool
    ready_for_external_verifier: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ChallengeReport:
    artifact: ProofArtifact
    challenges: tuple[str, ...]
    search_exhaustive: bool
    witness_found: bool
    epistemic_effect: str


@dataclass(frozen=True)
class PremortemReport:
    artifact: ProofArtifact
    risks: tuple[str, ...]
    negative_results: tuple[str, ...]
    baseline_required: bool


@dataclass(frozen=True)
class ConnectionEdge:
    tail: str
    head: str
    transport: Matrix

    @classmethod
    def scalar(cls, tail: str, head: str, transport: int = 1) -> "ConnectionEdge":
        return cls(tail, head, ((Fraction(transport),),))


@dataclass(frozen=True)
class ConnectionEnergyResult:
    energy: Scalar
    residuals: tuple[tuple[str, str, Vector], ...]
    edgewise_parallel: bool
    exact: bool
    unitarity_checked: bool
    theorem_applicable: bool
    hypotheses: tuple[str, ...]


@dataclass(frozen=True)
class LocalSection:
    chart_id: str
    domain: frozenset[str]
    values: tuple[tuple[str, str], ...]

    @classmethod
    def from_mapping(
        cls, chart_id: str, domain: Iterable[str], values: Mapping[str, str]
    ) -> "LocalSection":
        frozen_domain = frozenset(domain)
        if set(values) != set(frozen_domain):
            raise ValueError("a local section needs exactly one value per domain point")
        return cls(chart_id, frozen_domain, tuple(sorted(values.items())))

    def as_mapping(self) -> dict[str, str]:
        return dict(self.values)


@dataclass(frozen=True)
class GluingResult:
    compatible: bool
    cover_complete: bool
    candidate_global_section: tuple[tuple[str, str], ...] | None
    obstructions: tuple[str, ...]

    @property
    def gluable(self) -> bool:
        return self.compatible and self.cover_complete


@dataclass(frozen=True)
class BordonCycleResult:
    artifact: ProofArtifact
    phases: tuple[str, ...]
    energy: ConnectionEnergyResult | None
    gluing: GluingResult | None
    full_cycle: bool


class BeeNode:
    contract = NodeContract(
        name="Bee",
        operator="lossless source-span ingestion and deterministic normalization",
        metric="source/span hash preservation",
        may_emit=(Status.CAPTURED, Status.NORMALIZED),
        prohibition="similarity, repetition, or consensus is not semantic truth",
    )

    def capture(
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
        remainder: Remainder | None = None,
        constraints: Iterable[str] = (),
    ) -> ProofArtifact:
        return ProofArtifact(
            statement=statement,
            claim_kind=claim_kind,
            register=register,
            source=source,
            producer=self.contract.name,
            run_id=run_id,
            status=Status.CAPTURED,
            hypotheses=tuple(hypotheses),
            scope=scope,
            formal_statement=formal_statement,
            formal_environment_hash=formal_environment_hash,
            claim_language=claim_language,
            remainder=(
                remainder
                if remainder is not None
                else (
                    Remainder(unresolved_obligations=())
                    if claim_language is ClaimLanguage.FORMAL
                    else Remainder()
                )
            ),
            constraints=tuple(constraints),
            route_history=(self.contract.name,),
        )

    def normalize(self, artifact: ProofArtifact) -> ProofArtifact:
        normalized = " ".join(artifact.statement.split())
        return artifact.derive(
            producer=self.contract.name,
            status=Status.NORMALIZED,
            statement=normalized,
        )


class EmpressNode:
    contract = NodeContract(
        name="Empress",
        operator="generative extension and exact finite coboundary d",
        metric="new typed obligations plus exact edge residuals",
        may_emit=(Status.CANDIDATE, Status.PROOF_CANDIDATE),
        prohibition="d²=0 is not asserted without an explicit flat complex",
    )

    def expand(
        self,
        artifact: ProofArtifact,
        *,
        obligations: Iterable[str],
        nominate_for_proof: bool = False,
    ) -> ProofArtifact:
        status = Status.PROOF_CANDIDATE if nominate_for_proof else Status.CANDIDATE
        remainder = artifact.remainder.extend(unresolved_obligations=obligations)
        return artifact.derive(
            producer=self.contract.name,
            status=status,
            remainder=remainder,
        )

    @staticmethod
    def coboundary(
        vertex_values: Sequence[int | Fraction],
        oriented_edges: Sequence[tuple[int, int]],
    ) -> Vector:
        values = tuple(_fraction(value) for value in vertex_values)
        residuals: list[Fraction] = []
        for tail, head in oriented_edges:
            if min(tail, head) < 0 or max(tail, head) >= len(values):
                raise ValueError("edge endpoint outside vertex cochain")
            residuals.append(values[head] - values[tail])
        return tuple(residuals)


class EmperorNode:
    contract = NodeContract(
        name="Emperor",
        operator="constraint/dependency audit and exact transpose adjoint d*",
        metric="blocker count and adjoint-law residual",
        may_emit=(Status.CANDIDATE, Status.OPEN, Status.QUARANTINED),
        prohibition="an audit or symbolic adjoint cannot issue proof status",
    )

    def audit(self, artifact: ProofArtifact) -> AuditReport:
        blockers: list[str] = []
        if not artifact.validate_integrity():
            blockers.append("artifact integrity failed")
        if not artifact.source.content_hash or not artifact.source.span_hash:
            blockers.append("source provenance is incomplete")
        if artifact.formal_statement is None:
            blockers.append("prose-to-formal adequacy is unresolved")
        elif artifact.claim_language is ClaimLanguage.PROSE:
            blockers.append(
                "prose claim requires an independent formalization-adequacy verifier"
            )
        if artifact.status is Status.PROOF_CANDIDATE and not artifact.evidence:
            blockers.append("no replayable proof evidence is attached")
        audited = artifact.derive(
            producer=self.contract.name,
        )
        return AuditReport(
            artifact=audited,
            integrity_ok=audited.validate_integrity(),
            ready_for_external_verifier=not blockers,
            blockers=tuple(blockers),
        )

    @staticmethod
    def adjoint(
        edge_values: Sequence[int | Fraction],
        oriented_edges: Sequence[tuple[int, int]],
        vertex_count: int,
    ) -> Vector:
        if len(edge_values) != len(oriented_edges):
            raise ValueError("one edge-cochain value is required per edge")
        out = [Fraction(0) for _ in range(vertex_count)]
        for raw_value, (tail, head) in zip(edge_values, oriented_edges):
            if min(tail, head) < 0 or max(tail, head) >= vertex_count:
                raise ValueError("edge endpoint outside vertex space")
            value = _fraction(raw_value)
            out[tail] -= value
            out[head] += value
        return tuple(out)

    @classmethod
    def adjoint_law_holds(
        cls,
        vertex_values: Sequence[int | Fraction],
        edge_values: Sequence[int | Fraction],
        oriented_edges: Sequence[tuple[int, int]],
    ) -> bool:
        d_x = EmpressNode.coboundary(vertex_values, oriented_edges)
        d_star_y = cls.adjoint(edge_values, oriented_edges, len(vertex_values))
        x = tuple(_fraction(value) for value in vertex_values)
        y = tuple(_fraction(value) for value in edge_values)
        return _inner(d_x, y) == _inner(x, d_star_y)


class PandoraNode:
    contract = NodeContract(
        name="Pandora",
        operator="adversarial boundary/counterexample generation",
        metric="replayable counterexample yield and hypothesis coverage",
        may_emit=(Status.CANDIDATE, Status.TESTED, Status.OPEN),
        prohibition="failure to find a counterexample never raises claim status",
    )

    def challenge(
        self,
        artifact: ProofArtifact,
        *,
        challenges: Iterable[str],
        search_exhaustive: bool = False,
        witness_found: bool = False,
    ) -> ChallengeReport:
        challenge_tuple = tuple(challenges)
        effect = (
            "counterexample candidate; requires independent replay"
            if witness_found
            else "no truth-bearing transition"
        )
        remainder = artifact.remainder.extend(
            unresolved_obligations=challenge_tuple,
            uncovered_cases=()
            if search_exhaustive
            else ("Pandora search was not exhaustive",),
        )
        challenged = artifact.derive(
            producer=self.contract.name,
            remainder=remainder,
        )
        return ChallengeReport(
            artifact=challenged,
            challenges=challenge_tuple,
            search_exhaustive=search_exhaustive,
            witness_found=witness_found,
            epistemic_effect=effect,
        )


class ToposAINode:
    contract = NodeContract(
        name="Topos AI",
        operator="exact finite-cover restriction and overlap comparison",
        metric="coverage deficit and explicit overlap obstructions",
        may_emit=(Status.CANDIDATE, Status.OPEN),
        prohibition="pairwise resemblance or an incomplete cover is not gluing",
    )

    @staticmethod
    def glue(
        sections: Sequence[LocalSection], declared_domain: Iterable[str]
    ) -> GluingResult:
        domain = frozenset(declared_domain)
        covered = frozenset().union(*(section.domain for section in sections))
        obstructions: list[str] = []
        if covered != domain:
            missing = sorted(domain - covered)
            extra = sorted(covered - domain)
            if missing:
                obstructions.append(f"incomplete cover; missing {missing}")
            if extra:
                obstructions.append(f"cover exceeds declared domain at {extra}")
        glued: dict[str, str] = {}
        compatible = True
        for section in sections:
            values = section.as_mapping()
            for point in section.domain:
                value = values[point]
                if point in glued and glued[point] != value:
                    compatible = False
                    obstructions.append(
                        f"overlap conflict at {point}: {glued[point]!r} != {value!r} "
                        f"in chart {section.chart_id}"
                    )
                else:
                    glued[point] = value
        cover_complete = covered == domain
        candidate = tuple(sorted(glued.items())) if compatible and cover_complete else None
        return GluingResult(
            compatible=compatible,
            cover_complete=cover_complete,
            candidate_global_section=candidate,
            obstructions=tuple(obstructions),
        )

    def review_artifact(
        self, artifact: ProofArtifact, gluing: GluingResult | None
    ) -> ProofArtifact:
        if gluing is None:
            remainder = artifact.remainder.extend(uncovered_cases=(
                "Topos descent not evaluated: no explicit cover/restriction data",
            ))
        elif gluing.gluable:
            remainder = artifact.remainder.extend(uncovered_cases=(
                "compatible finite gluing is only a candidate global section; "
                "semantic verification remains external",
            ))
        else:
            remainder = artifact.remainder.extend(
                unresolved_obligations=gluing.obstructions
            )
        return artifact.derive(
            producer=self.contract.name,
            remainder=remainder,
        )


class BordonSymphonyNode:
    contract = NodeContract(
        name="Bordon Symphony",
        operator="ten-phase compatibility cycle and exact connection energy",
        metric="edge residuals, energy, holonomy, and full-phase trace",
        may_emit=(Status.CANDIDATE, Status.TESTED, Status.OPEN),
        prohibition="low/zero energy is compatibility, not theorem truth",
    )

    PHASES = (
        "INHALE",
        "SUPERPOSE",
        "ANNEAL",
        "HOLOPORT",
        "EXHALE",
        "LISTEN",
        "MEASURE HOLONOMY",
        "REGLUE",
        "MOVE FRAME",
        "CONTINUE",
    )

    @staticmethod
    def connection_energy(
        sections: Mapping[str, Sequence[int | Fraction]],
        edges: Sequence[ConnectionEdge],
        *,
        require_unitary: bool = True,
    ) -> ConnectionEnergyResult:
        vectors: dict[str, Vector] = {
            name: tuple(_fraction(value) for value in vector)
            for name, vector in sections.items()
        }
        residuals: list[tuple[str, str, Vector]] = []
        total = Fraction(0)
        for edge in edges:
            if edge.tail not in vectors or edge.head not in vectors:
                raise ValueError("connection edge references a missing section")
            tail = vectors[edge.tail]
            head = vectors[edge.head]
            if len(tail) != len(head):
                raise ValueError("fiber dimensions differ")
            if len(edge.transport) != len(tail):
                raise ValueError("transport dimension differs from fiber")
            if require_unitary and not _is_orthogonal(edge.transport):
                raise ValueError(
                    "the finite Resonance theorem requires exact unitary transports"
                )
            transported = _matvec(edge.transport, tail)
            residual = tuple(b - a for a, b in zip(transported, head))
            residuals.append((edge.tail, edge.head, residual))
            total += _inner(residual, residual)
        total /= 2
        return ConnectionEnergyResult(
            energy=total,
            residuals=tuple(residuals),
            edgewise_parallel=all(
                all(component == 0 for component in residual)
                for _, _, residual in residuals
            ),
            exact=True,
            unitarity_checked=require_unitary,
            theorem_applicable=require_unitary,
            hypotheses=(
                (
                    "finite graph",
                    "positive-definite rational fibers",
                    "exact orthogonal transports",
                )
                if require_unitary
                else (
                    "finite graph",
                    "positive-definite rational fibers",
                    "arbitrary declared linear transports; Resonance theorem disabled",
                )
            ),
        )

    def cycle(
        self,
        artifact: ProofArtifact,
        *,
        energy: ConnectionEnergyResult | None = None,
        gluing: GluingResult | None = None,
    ) -> BordonCycleResult:
        before = (
            artifact.claim_id,
            artifact.source.content_hash,
            artifact.source.span_hash,
            artifact.constraints,
            artifact.remainder,
        )
        evidence: tuple[Evidence, ...] = ()
        remainder = artifact.remainder
        if energy is None:
            remainder = remainder.extend(
                uncovered_cases=(
                    "connection energy not computed: explicit Hilbert-fiber data absent",
                )
            )
        else:
            payload = {
                "energy": energy.energy,
                "residuals": energy.residuals,
                "hypotheses": energy.hypotheses,
            }
            result_hash = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
            evidence = (
                Evidence(
                    kind=EvidenceKind.EXACT_COMPUTATION,
                    method="finite rational connection energy",
                    input_hash=artifact.artifact_id,
                    output_hash=result_hash,
                    result=(
                        f"energy={energy.energy}; "
                        f"edgewise_parallel={energy.edgewise_parallel}"
                    ),
                    assumptions_checked=energy.hypotheses,
                ),
            )
        if gluing is not None and not gluing.gluable:
            remainder = remainder.extend(
                unresolved_obligations=gluing.obstructions
            )
        cycled = artifact.derive(
            producer=self.contract.name,
            evidence=evidence,
            remainder=remainder,
            phase_trace=self.PHASES,
        )
        after = (
            cycled.claim_id,
            cycled.source.content_hash,
            cycled.source.span_hash,
            cycled.constraints,
            artifact.remainder,
        )
        if before != after:
            raise RuntimeError("HOLOPORT failed to preserve claim/provenance/constraints")
        return BordonCycleResult(
            artifact=cycled,
            phases=self.PHASES,
            energy=energy,
            gluing=gluing,
            full_cycle=cycled.phase_trace == self.PHASES,
        )


class UTAINode:
    contract = NodeContract(
        name="UTAI",
        operator="pre-mortem, disconfirmation, scope and negative-result ledger",
        metric="open-risk coverage and baseline comparison",
        may_emit=(Status.CANDIDATE, Status.OPEN, Status.QUARANTINED),
        prohibition="a governance policy or closure heuristic is not a theorem",
    )

    def premortem(
        self,
        artifact: ProofArtifact,
        *,
        risks: Iterable[str],
        negative_results: Iterable[str] = (),
        baseline_required: bool = True,
    ) -> PremortemReport:
        risk_tuple = tuple(risks)
        negative_tuple = tuple(negative_results)
        remainder = artifact.remainder.extend(
            uncovered_cases=risk_tuple,
            competing_interpretations=negative_tuple,
        )
        reviewed = artifact.derive(
            producer=self.contract.name,
            remainder=remainder,
        )
        return PremortemReport(
            artifact=reviewed,
            risks=risk_tuple,
            negative_results=negative_tuple,
            baseline_required=baseline_required,
        )
