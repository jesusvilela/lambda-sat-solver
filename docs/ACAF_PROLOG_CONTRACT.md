# LambdaSAT x ACAF-Prolog | Typed decision/count contract v1

One proposition; two implementations. No untyped evidence transport.

The module backend/acaf_interop.py exports JSON-serializable acaf-sat-v1 records for the separate ETH Prolog audit (Dojo-1/ETH-Refutation-Prolog-reproduction-and-adversarial-audit). Its frame-only code never invokes Kissat or an external proof checker. A receiving Prolog program independently counts all assignments on bounded cases.

## Fields

- schema: acaf-sat-v1.
- case_id: nonempty trace label.
- role: semantic_cnf or provenance_only.
- cnf: an object with n and clauses (signed integer lists; empty and repeated clauses allowed).
- count_universe: declared_variables (not only occurring variables).
- lambda.status: SAT, UNSAT, UNKNOWN, or NOT_APPLICABLE.
- lambda.certification: model_replay, local_frame_derivation, or none.
- lambda.model: list of [variable_id, bit] pairs for a SAT witness.

No exact count is supplied by LambdaSAT: Prolog computes it without trusting a producer count. SAT models are replayed on original clauses. Frame-UNSAT certificates are local 2-SAT, GF(2), or counting derivation claims; they are not independently checked DRAT proofs.

## Typed remainder

Only role=semantic_cnf can be used as an exact counting input. An empty CNF returned by a parity-provenance routine may be satisfiable even though its source lambda formula is false. Export it as role=provenance_only; the independent Prolog counter must reject it. Tseitin gate variables, auxiliary-variable extensions, and parity shadows need explicit logical and multiplicity transport.

## Reproduce

python -m unittest backend.tests.test_acaf_interop -v

A separate, pinned GitHub Actions job in the Prolog repo runs the full dual implementation comparison. UNKNOWN is a permitted abstention, not a negative verdict. This project does not assert any general subexponential-time algorithm or independent Lean proof.