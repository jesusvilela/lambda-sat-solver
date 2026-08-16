"""Append-only JSONL event ledger for proof-mesh runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .artifacts import ProofArtifact, Status, canonical_json, transition_allowed


@dataclass(frozen=True)
class LedgerEvent:
    run_id: str
    sequence: int
    event_type: str
    node: str
    artifact_id: str
    claim_id: str
    status: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "node": self.node,
            "artifact_id": self.artifact_id,
            "claim_id": self.claim_id,
            "status": self.status,
            "payload": self.payload,
        }


class JsonlLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: LedgerEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


class ArtifactStore:
    """Gate-side content store for exact, append-only artifact lineages.

    Research nodes should receive no reference to this capability. The store
    snapshots canonical payloads, so later object mutation is detected.
    """

    def __init__(self):
        self.__snapshots: dict[str, str] = {}
        self.__parents: dict[str, tuple[str, ...]] = {}

    RESEARCH_NODES = frozenset(
        {
            "Bee",
            "Empress",
            "Emperor",
            "Pandora",
            "Bordon Symphony",
            "UTAI",
            "Topos AI",
        }
    )

    @staticmethod
    def _is_prefix(before: list[Any], after: list[Any]) -> bool:
        return after[: len(before)] == before

    def _validate_transition(
        self, parent: dict[str, Any], child: dict[str, Any]
    ) -> None:
        expected_parents = [
            *parent["parent_artifact_ids"],
            parent["artifact_id"],
        ]
        if child["parent_artifact_ids"] != expected_parents:
            raise ValueError("child parent chain is not the exact append-only lineage")
        if not transition_allowed(
            Status(parent["status"]), Status(child["status"])
        ):
            raise ValueError("child uses a forbidden epistemic status transition")
        if child["producer"] not in self.RESEARCH_NODES:
            raise ValueError("child producer is not a deployed research node")
        if child["route_history"] != [
            *parent["route_history"],
            child["producer"],
        ]:
            raise ValueError("route history is not an exact append-only hop")
        for field in ("source", "run_id", "schema_version"):
            if child[field] != parent[field]:
                raise ValueError(f"ordinary child changed immutable field {field}")
        for field in ("evidence", "phase_trace"):
            if not self._is_prefix(parent[field], child[field]):
                raise ValueError(f"child erased or rewrote append-only field {field}")
        if not set(parent["constraints"]).issubset(child["constraints"]):
            raise ValueError("child erased an inherited constraint")
        remainder_fields = (
            "missing_hypotheses",
            "unresolved_obligations",
            "uncovered_cases",
            "ambiguity_set",
            "competing_interpretations",
        )
        for field in remainder_fields:
            if not set(parent["remainder"][field]).issubset(
                child["remainder"][field]
            ):
                raise ValueError(f"child erased remainder field {field}")
        if child["claim_id"] != parent["claim_id"] and child["evidence"]:
            raise ValueError("child migrated evidence to a changed claim")

    def register(self, artifact: ProofArtifact) -> None:
        if not artifact.validate_integrity():
            raise ValueError("cannot register an artifact with failed integrity")
        if artifact.parent_artifact_ids:
            missing = [
                parent
                for parent in artifact.parent_artifact_ids
                if parent not in self.__snapshots
            ]
            if missing:
                raise ValueError(f"artifact lineage has unregistered parents: {missing}")
            parent_payload = json.loads(
                self.__snapshots[artifact.parent_artifact_ids[-1]]
            )
            self._validate_transition(parent_payload, artifact.to_dict())
        elif artifact.status is not Status.CAPTURED:
            raise ValueError("an unparented artifact-store root must be captured")
        elif artifact.producer != "Bee" or artifact.route_history != ("Bee",):
            raise ValueError("a root ingestion must be a single Bee capture")
        snapshot = canonical_json(artifact.to_dict())
        existing = self.__snapshots.get(artifact.artifact_id)
        if existing is not None and existing != snapshot:
            raise ValueError("artifact id collision or post-registration mutation")
        self.__snapshots[artifact.artifact_id] = snapshot
        self.__parents[artifact.artifact_id] = artifact.parent_artifact_ids

    def contains_exact(self, artifact: ProofArtifact) -> bool:
        try:
            if not artifact.validate_integrity():
                return False
            return self.__snapshots.get(artifact.artifact_id) == canonical_json(
                artifact.to_dict()
            )
        except (TypeError, ValueError):
            return False

    def lineage_complete(self, artifact: ProofArtifact) -> bool:
        if not self.contains_exact(artifact):
            return False
        return all(
            parent in self.__snapshots for parent in artifact.parent_artifact_ids
        )
