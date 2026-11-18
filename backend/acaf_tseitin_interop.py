"""ACAF λSAT -> Prolog: direct β-normal Boolean Tseitin *count* audit.

Do not use lambda_sat(term).cnf for this protocol: its parity projection is
explicitly provenance-only in some regimes. This exporter always calls the
definitional tseitin_encode on the β-normal Boolean AST and marks it as such.

The original free-variable universe and normalized free-variable universe are
both retained; β-reduction may erase variables. The count-transport correction
is 2**(original_n-normal_n), not an unconditional raw count identity.
"""
from __future__ import annotations

from itertools import product
from typing import Any

from .lambda_sat import (
    BExpr, beta_normalize, free_vars, eval_bool, tseitin_encode,
)

SCHEMA = "acaf-tseitin-v1"


def export_tseitin_case(
    term: BExpr, case_id: str, *, max_original_free: int = 5,
    max_cnf_vars: int = 12, max_beta_steps: int = 1000
) -> dict[str, Any]:
    """Export bounded proof obligations, not a claim that Lean verified them.

    truth_rows are indexed over ALL *original* free variables in lexical order,
    including those erased during β-reduction. No exact #CNF is supplied.
    The receiving Prolog oracle independently counts extensions per truth row.
    """
    if not isinstance(case_id, str) or not case_id or len(case_id) > 128:
        raise ValueError("case_id must be a short, nonempty identifier")
    if not isinstance(term, BExpr):
        raise TypeError("expected λSAT BExpr")
    original_free = sorted(free_vars(term))
    if len(original_free) > max_original_free:
        raise ValueError("too many original free variables for exhaustive source table")
    normal = beta_normalize(term, max_steps=max_beta_steps)
    normal_free = sorted(free_vars(normal))
    if not set(normal_free).issubset(original_free):
        raise AssertionError("β-normalization invented a free variable")
    # This is a gate *definition*, never the frame-native parity ghost CNF.
    cnf, remainder, free_ids = tseitin_encode(normal)
    if cnf.num_vars > max_cnf_vars:
        raise ValueError("Tseitin CNF exceeds bounded exact-extension audit budget")
    if set(free_ids) != set(normal_free):
        raise AssertionError("Tseitin variable mapping lost a normalized free variable")
    if len(set(free_ids.values())) != len(free_ids):
        raise AssertionError("Tseitin reused distinct source variable ids")
    if any(type(v) is not int or not 1 <= v <= cnf.num_vars
           for v in free_ids.values()):
        raise AssertionError("invalid free-to-CNF variable id")
    truth_rows = []
    for bits in product((0, 1), repeat=len(original_free)):
        env = {name: bool(bit) for name, bit in zip(original_free, bits)}
        truth_rows.append({"bits": list(bits), "truth": int(eval_bool(normal, env))})
    return {
        "schema": SCHEMA,
        "case_id": case_id,
        "role": "semantic_gate_cnf",
        "transport": "beta_then_definitional_tseitin",
        "source": {
            "term_repr": repr(term),
            "original_free": original_free,
            "normal_free": normal_free,
            "truth_rows": truth_rows,
        },
        "gate": {
            "n": cnf.num_vars,
            "clauses": [list(c) for c in cnf.clauses],
            "free_var_ids": [[name, var_id] for name, var_id in sorted(free_ids.items())],
            "provenance_clause_count": len(remainder),
        }
    }
