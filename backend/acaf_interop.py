"""λSAT to ACAF-Prolog v1: typed semantic-CNF exchange.

This exporter never returns an exact count. The receiving Prolog oracle owns
that computation. Provenance-only CNFs are explicitly marked, so their
clauses cannot be mistaken for a semantics-preserving representation.
"""
from __future__ import annotations
from typing import Any
from .cnf_utils import CNFFormula, verify_model

SCHEMA = "acaf-sat-v1"


def _validate_cnf(formula: CNFFormula) -> None:
    n = formula.num_vars
    if type(n) is not int or n < 0:
        raise ValueError("declared variable count must be a nonnegative integer")
    if not isinstance(formula.clauses, list):
        raise ValueError("clauses must be a list")
    for clause in formula.clauses:
        if not isinstance(clause, list):
            raise ValueError("each clause must be a list")
        for lit in clause:
            if type(lit) is not int or lit == 0 or abs(lit) > n:
                raise ValueError("literal outside declared universe")


def export_case(formula: CNFFormula, case_id: str, *,
                role: str = "semantic_cnf", run_frame: bool = True) -> dict[str, Any]:
    """Produce portable JSON for independent exact counting and falsification.

    The certificate is scoped: frame-UNSAT is a local algebraic derivation, not
    an externally checked DRAT proof. SAT models are replayed on source CNF.
    UNKNOWN is abstention and must not be interpreted as UNSAT.
    """
    if not isinstance(case_id, str) or not case_id or len(case_id) > 128:
        raise ValueError("case_id must be a short nonempty string")
    if role not in ("semantic_cnf", "provenance_only"):
        raise ValueError("unrecognized semantic role")
    _validate_cnf(formula)
    decision: dict[str, Any] = {
        "status": "NOT_APPLICABLE" if role == "provenance_only" else "UNKNOWN",
        "method": "none", "certification": "none", "model": []
    }
    if role == "semantic_cnf" and run_frame:
        from .frame_solver import frame_solve
        result = frame_solve(formula)
        if result.status == "SAT":
            if not result.certified or result.model is None or not verify_model(formula, result.model):
                raise AssertionError("unreplayed SAT witness")
            decision = {
                "status": "SAT", "method": result.resolved_by,
                "certification": "model_replay",
                "model": [[int(v), int(bool(bit))] for v, bit in sorted(result.model.items())]
            }
        elif result.status == "UNSAT":
            if not result.certified or result.resolved_by not in ("2sat", "parity", "counting"):
                raise AssertionError("unscoped frame refutation")
            decision = {
                "status": "UNSAT", "method": result.resolved_by,
                "certification": "local_frame_derivation", "model": []
            }
        elif result.status != "CDCL_NEEDED":
            raise AssertionError("unknown λSAT status")
    return {
        "schema": SCHEMA, "case_id": case_id, "role": role,
        "cnf": {"n": formula.num_vars, "clauses": [list(c) for c in formula.clauses]},
        "count_universe": "declared_variables",
        "lambda": decision
    }
