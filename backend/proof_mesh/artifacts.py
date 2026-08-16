"""Immutable proof artifacts and their epistemic state machine.

Research-node output is never a proof certificate. A final ``PROVED`` or
``REFUTED`` artifact can only be built by the promotion gate using a
replayable external-verifier attestation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass, replace
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "proof-hypermesh/v1"


class Status(str, Enum):
    CAPTURED = "captured"
    NORMALIZED = "normalized"
    CANDIDATE = "candidate"
    TESTED = "tested"
    PROOF_CANDIDATE = "proof_candidate"
    PROVED = "proved"
    REFUTED = "refuted"
    OPEN = "open"
    QUARANTINED = "quarantined"


class ClaimKind(str, Enum):
    DEFINITION = "definition"
    THEOREM = "theorem"
    LEMMA = "lemma"
    CONJECTURE = "conjecture"
    COUNTEREXAMPLE = "counterexample"
    COMPUTATION = "computation"
    HEURISTIC = "heuristic"


class EpistemicRegister(str, Enum):
    IMPORTED_MATH = "imported_math"
    DEFINED_THEORY = "defined_theory"
    PROVED_CORE = "proved_core"
    INTERPRETIVE_CONJECTURAL = "interpretive_conjectural"


class ClaimLanguage(str, Enum):
    PROSE = "prose"
    FORMAL = "formal"


class EvidenceKind(str, Enum):
    FORMAL_PROOF = "formal_proof"
    EXACT_WITNESS = "exact_witness"
    EXACT_COUNTEREXAMPLE = "exact_counterexample"
    FINITE_EXHAUSTION = "finite_exhaustion"
    NUMERICAL_TEST = "numerical_test"
    HEURISTIC_ARGUMENT = "heuristic_argument"
    CITATION = "citation"
    EXACT_COMPUTATION = "exact_computation"


FINAL_STATUSES = frozenset({Status.PROVED, Status.REFUTED})

_ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.CAPTURED: frozenset(
        {Status.NORMALIZED, Status.CANDIDATE, Status.OPEN, Status.QUARANTINED}
    ),
    Status.NORMALIZED: frozenset(
        {
            Status.CANDIDATE,
            Status.TESTED,
            Status.PROOF_CANDIDATE,
            Status.OPEN,
            Status.QUARANTINED,
        }
    ),
    Status.CANDIDATE: frozenset(
        {
            Status.TESTED,
            Status.PROOF_CANDIDATE,
            Status.OPEN,
            Status.QUARANTINED,
            Status.REFUTED,
        }
    ),
    Status.TESTED: frozenset(
        {
            Status.PROOF_CANDIDATE,
            Status.OPEN,
            Status.QUARANTINED,
            Status.REFUTED,
        }
    ),
    Status.PROOF_CANDIDATE: frozenset(
        {Status.PROVED, Status.REFUTED, Status.OPEN, Status.QUARANTINED}
    ),
    Status.OPEN: frozenset(
        {Status.CANDIDATE, Status.TESTED, Status.PROOF_CANDIDATE, Status.QUARANTINED}
    ),
    Status.QUARANTINED: frozenset({Status.OPEN}),
    Status.PROVED: frozenset({Status.QUARANTINED}),
    Status.REFUTED: frozenset({Status.QUARANTINED}),
}


def transition_allowed(current: Status, following: Status) -> bool:
    return following == current or following in _ALLOWED_TRANSITIONS[current]


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(key): _canonical(val) for key, val in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=repr)
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SourceLocator:
    path_or_url: str
    content_hash: str
    span_hash: str
    start_line: int | None = None
    end_line: int | None = None
    symbol: str | None = None

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
        symbol: str | None = None,
    ) -> "SourceLocator":
        resolved = Path(path).expanduser().resolve()
        payload = resolved.read_bytes()
        lines = payload.splitlines(keepends=True)
        if start_line is None:
            span = payload
        else:
            if start_line < 1:
                raise ValueError("start_line is one-based")
            actual_end = end_line if end_line is not None else start_line
            if actual_end < start_line or actual_end > max(len(lines), 1):
                raise ValueError("invalid source line span")
            span = b"".join(lines[start_line - 1 : actual_end])
        return cls(
            path_or_url=str(resolved),
            content_hash=sha256(payload).hexdigest(),
            span_hash=sha256(span).hexdigest(),
            start_line=start_line,
            end_line=end_line,
            symbol=symbol,
        )

    @classmethod
    def from_text(cls, label: str, text: str) -> "SourceLocator":
        payload = text.encode("utf-8")
        content_hash = sha256(payload).hexdigest()
        return cls(label, content_hash, content_hash)


@dataclass(frozen=True)
class Remainder:
    missing_hypotheses: tuple[str, ...] = ()
    unresolved_obligations: tuple[str, ...] = ("semantic adequacy not yet verified",)
    uncovered_cases: tuple[str, ...] = ()
    ambiguity_set: tuple[str, ...] = ()
    competing_interpretations: tuple[str, ...] = ()

    def is_nonempty(self) -> bool:
        return any(
            (
                self.missing_hypotheses,
                self.unresolved_obligations,
                self.uncovered_cases,
                self.ambiguity_set,
                self.competing_interpretations,
            )
        )

    def proof_blockers(self) -> tuple[str, ...]:
        return (*self.missing_hypotheses, *self.unresolved_obligations)

    def extend(
        self,
        *,
        missing_hypotheses: Iterable[str] = (),
        unresolved_obligations: Iterable[str] = (),
        uncovered_cases: Iterable[str] = (),
        ambiguity_set: Iterable[str] = (),
        competing_interpretations: Iterable[str] = (),
    ) -> "Remainder":
        def merged(current: tuple[str, ...], additions: Iterable[str]) -> tuple[str, ...]:
            return tuple(dict.fromkeys((*current, *(item for item in additions if item))))

        return Remainder(
            missing_hypotheses=merged(self.missing_hypotheses, missing_hypotheses),
            unresolved_obligations=merged(
                self.unresolved_obligations, unresolved_obligations
            ),
            uncovered_cases=merged(self.uncovered_cases, uncovered_cases),
            ambiguity_set=merged(self.ambiguity_set, ambiguity_set),
            competing_interpretations=merged(
                self.competing_interpretations, competing_interpretations
            ),
        )


@dataclass(frozen=True)
class Evidence:
    kind: EvidenceKind
    method: str
    input_hash: str
    output_hash: str
    result: str
    certificate: str | None = None
    replay_recipe: str | None = None
    checker_name_version: str | None = None
    checker_environment_hash: str | None = None
    assumptions_checked: tuple[str, ...] = ()


@dataclass(frozen=True)
class Attestation:
    claim_id: str
    verifier_id: str
    verdict: Status
    certificate_kind: str
    certificate_digest: str
    replay_recipe: str
    checker_environment_hash: str
    input_hash: str
    independent_of: str
    assumptions: tuple[str, ...] = ()
    adequacy_verifier_id: str | None = None
    adequacy_certificate_digest: str | None = None
    adequacy_independent_of: str | None = None
    adequacy_method: str | None = None
    adequacy_replay_recipe: str | None = None
    adequacy_checker_environment_hash: str | None = None
    gate_id: str = ""
    signature: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in FINAL_STATUSES:
            raise ValueError("an attestation verdict must be proved or refuted")
        required = (
            self.claim_id,
            self.verifier_id,
            self.certificate_kind,
            self.certificate_digest,
            self.replay_recipe,
            self.checker_environment_hash,
            self.input_hash,
            self.independent_of,
            self.gate_id,
            self.signature,
        )
        if any(not value for value in required):
            raise ValueError("attestations require replayable, attributed evidence")
        adequacy_fields = (
            self.adequacy_verifier_id,
            self.adequacy_certificate_digest,
            self.adequacy_independent_of,
            self.adequacy_method,
            self.adequacy_replay_recipe,
            self.adequacy_checker_environment_hash,
        )
        if any(value is not None for value in adequacy_fields) and not all(
            adequacy_fields
        ):
            raise ValueError(
                "formalization adequacy metadata must be complete or entirely absent"
            )


@dataclass(frozen=True)
class ProofArtifact:
    statement: str
    claim_kind: ClaimKind
    register: EpistemicRegister
    source: SourceLocator
    producer: str
    run_id: str
    status: Status = Status.CAPTURED
    hypotheses: tuple[str, ...] = ()
    scope: str = ""
    formal_statement: str | None = None
    formal_environment_hash: str | None = None
    claim_language: ClaimLanguage = ClaimLanguage.PROSE
    parent_artifact_ids: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    remainder: Remainder = field(default_factory=Remainder)
    constraints: tuple[str, ...] = ()
    route_history: tuple[str, ...] = ()
    phase_trace: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    claim_id: str = field(init=False)
    artifact_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement must be nonempty")
        if self.claim_language is ClaimLanguage.FORMAL:
            if self.formal_statement is None:
                raise ValueError("a formal claim requires a formal statement identifier")
            if self.statement.strip() != self.formal_statement.strip():
                raise ValueError(
                    "formal-mode artifacts must identify exactly the checked declaration; "
                    "use prose mode plus an adequacy verifier for paraphrases"
                )
        if not self.source.content_hash or not self.source.span_hash:
            raise ValueError("source provenance must be content-addressed")
        claim_payload = {
            "schema_version": self.schema_version,
            "statement": self.statement.strip(),
            "formal_statement": self.formal_statement,
            "formal_environment_hash": self.formal_environment_hash,
            "claim_language": self.claim_language,
            "hypotheses": self.hypotheses,
            "scope": self.scope,
        }
        claim_id = digest(claim_payload)
        object.__setattr__(self, "claim_id", claim_id)
        if self.status in FINAL_STATUSES:
            raise ValueError(
                "research artifacts cannot carry a final status; "
                "use a separately trust-verified PromotedArtifact envelope"
            )
        artifact_payload = {
            "claim_id": claim_id,
            "claim_kind": self.claim_kind,
            "register": self.register,
            "source": self.source,
            "producer": self.producer,
            "run_id": self.run_id,
            "status": self.status,
            "parents": self.parent_artifact_ids,
            "evidence": self.evidence,
            "remainder": self.remainder,
            "constraints": self.constraints,
            "route_history": self.route_history,
            "phase_trace": self.phase_trace,
        }
        object.__setattr__(self, "artifact_id", digest(artifact_payload))

    def derive(
        self,
        *,
        producer: str,
        status: Status | None = None,
        statement: str | None = None,
        claim_kind: ClaimKind | None = None,
        register: EpistemicRegister | None = None,
        hypotheses: tuple[str, ...] | None = None,
        scope: str | None = None,
        formal_statement: str | None = None,
        formal_environment_hash: str | None = None,
        claim_language: ClaimLanguage | None = None,
        evidence: Iterable[Evidence] = (),
        remainder: Remainder | None = None,
        constraints: tuple[str, ...] | None = None,
        phase_trace: tuple[str, ...] | None = None,
    ) -> "ProofArtifact":
        next_status = status if status is not None else self.status
        if not transition_allowed(self.status, next_status):
            raise ValueError(
                f"forbidden status transition {self.status.value} -> "
                f"{next_status.value}"
            )
        if next_status in FINAL_STATUSES:
            raise PermissionError(
                "research artifacts cannot finalize; use a trusted promotion envelope"
            )
        if remainder is not None:
            fields = (
                "missing_hypotheses",
                "unresolved_obligations",
                "uncovered_cases",
                "ambiguity_set",
                "competing_interpretations",
            )
            for name in fields:
                before = set(getattr(self.remainder, name))
                after = set(getattr(remainder, name))
                if not before.issubset(after):
                    raise ValueError(
                        f"ordinary derivation cannot erase remainder field {name}; "
                        "discharge requires a separately attested transition"
                    )
        if constraints is not None and not set(self.constraints).issubset(constraints):
            raise ValueError(
                "ordinary derivation cannot erase constraints; "
                "discharge requires a separately attested transition"
            )
        claim_fields_changed = any(
            (
                statement is not None and statement != self.statement,
                hypotheses is not None and hypotheses != self.hypotheses,
                scope is not None and scope != self.scope,
                formal_statement is not None
                and formal_statement != self.formal_statement,
                formal_environment_hash is not None
                and formal_environment_hash != self.formal_environment_hash,
                claim_language is not None and claim_language != self.claim_language,
            )
        )
        if claim_fields_changed and self.evidence:
            raise ValueError(
                "evidence cannot migrate automatically to a changed claim"
            )
        return replace(
            self,
            statement=statement if statement is not None else self.statement,
            claim_kind=claim_kind if claim_kind is not None else self.claim_kind,
            register=register if register is not None else self.register,
            producer=producer,
            status=next_status,
            hypotheses=hypotheses if hypotheses is not None else self.hypotheses,
            scope=scope if scope is not None else self.scope,
            formal_statement=(
                formal_statement if formal_statement is not None else self.formal_statement
            ),
            formal_environment_hash=(
                formal_environment_hash
                if formal_environment_hash is not None
                else self.formal_environment_hash
            ),
            claim_language=(
                claim_language if claim_language is not None else self.claim_language
            ),
            parent_artifact_ids=(*self.parent_artifact_ids, self.artifact_id),
            evidence=(*self.evidence, *tuple(evidence)),
            remainder=remainder if remainder is not None else self.remainder,
            constraints=constraints if constraints is not None else self.constraints,
            route_history=(*self.route_history, producer),
            phase_trace=phase_trace if phase_trace is not None else self.phase_trace,
        )

    def validate_integrity(self) -> bool:
        rebuilt = replace(self)
        return (
            rebuilt.claim_id == self.claim_id
            and rebuilt.artifact_id == self.artifact_id
            and bool(self.source.content_hash)
            and bool(self.source.span_hash)
        )

    def to_dict(self) -> dict[str, Any]:
        payload = _canonical(self)
        if not isinstance(payload, dict):
            raise TypeError("canonical artifact payload should be a dictionary")
        payload["claim_id"] = self.claim_id
        payload["artifact_id"] = self.artifact_id
        return payload
