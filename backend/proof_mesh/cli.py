"""Command-line entry point for deterministic proof-distillation runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .artifacts import (
    ClaimKind,
    ClaimLanguage,
    EpistemicRegister,
    Remainder,
    SourceLocator,
)
from .ledger import JsonlLedger
from .nodes import LocalSection
from .orchestrator import ProofHypermesh


def _source_from_config(item: dict[str, Any]) -> SourceLocator:
    source = item["source"]
    if "path" in source:
        return SourceLocator.from_path(
            source["path"],
            start_line=source.get("start_line"),
            end_line=source.get("end_line"),
            symbol=source.get("symbol"),
        )
    return SourceLocator.from_text(source["label"], source["text"])


def run_config(config: dict[str, Any], ledger_path: str | None = None) -> dict[str, Any]:
    ledger = JsonlLedger(ledger_path) if ledger_path else None
    mesh = ProofHypermesh(ledger=ledger)
    runs = []
    for index, item in enumerate(config.get("claims", ()), start=1):
        remainder_config = item.get("remainder", {})
        remainder = Remainder(
            missing_hypotheses=tuple(remainder_config.get("missing_hypotheses", ())),
            unresolved_obligations=tuple(
                remainder_config.get(
                    "unresolved_obligations",
                    ("semantic adequacy not yet verified",),
                )
            ),
            uncovered_cases=tuple(remainder_config.get("uncovered_cases", ())),
            ambiguity_set=tuple(remainder_config.get("ambiguity_set", ())),
            competing_interpretations=tuple(
                remainder_config.get("competing_interpretations", ())
            ),
        )
        local_sections = tuple(
            LocalSection.from_mapping(
                section["chart_id"],
                section["domain"],
                section["values"],
            )
            for section in item.get("local_sections", ())
        )
        run = mesh.distill(
            statement=item["statement"],
            source=_source_from_config(item),
            run_id=item.get("run_id", f"{config.get('run_id', 'mesh')}-{index}"),
            claim_kind=ClaimKind(item.get("claim_kind", "conjecture")),
            register=EpistemicRegister(
                item.get("register", "interpretive_conjectural")
            ),
            hypotheses=tuple(item.get("hypotheses", ())),
            scope=item.get("scope", ""),
            formal_statement=item.get("formal_statement"),
            formal_environment_hash=item.get("formal_environment_hash"),
            claim_language=ClaimLanguage(item.get("claim_language", "prose")),
            initial_remainder=remainder,
            constraints=tuple(item.get("constraints", ())),
            obligations=tuple(item.get("obligations", ())),
            nominate_for_proof=bool(item.get("nominate_for_proof", False)),
            challenges=tuple(item.get("challenges", ())),
            search_exhaustive=bool(item.get("search_exhaustive", False)),
            witness_found=bool(item.get("witness_found", False)),
            local_sections=local_sections,
            declared_domain=tuple(item.get("declared_domain", ())),
            risks=tuple(item.get("risks", ())),
            negative_results=tuple(item.get("negative_results", ())),
        )
        runs.append(run.to_dict())
    return {
        "schema": "proof-hypermesh-run/v1",
        "node_manifest": mesh.node_manifest(),
        "run_count": len(runs),
        "runs": runs,
        "warning": (
            "No research node can certify a claim. Final status requires a "
            "separate allowlisted verifier report and PromotionGate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="JSON experiment configuration")
    parser.add_argument("--output", required=True, help="result JSON path")
    parser.add_argument("--ledger", help="optional append-only JSONL ledger")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = run_config(config, args.ledger)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
