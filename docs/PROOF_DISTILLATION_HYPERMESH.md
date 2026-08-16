# Proof-Distillation Hypermesh

## Status

This is a local, sequential deployment of seven proof-research roles:

1. Bee
2. Empress
3. Pandora
4. Emperor
5. Topos AI
6. Bordon Symphony
7. UTAI

They extract, extend, attack, audit, compare, and preserve mathematical
claims. None can certify one. Final certification is a separate
trust-anchored operation.

The implementation is additive. It does not modify the existing SAT decision
path or import itself into the active VDIS root.

## Why this shape

The design operationalizes four boundaries:

- recognition is not verification;
- candidate gluing is not a valid global section;
- the proposer is not the verifier;
- an observer is not a proof object.

It also implements the manuscript's Emperor/Empress adjoint metaphor on an
exact finite cochain complex, the Bordon ten-phase cycle, explicit local-cover
gluing, and a persistent remainder.

## Node contracts

| Node | Operator | Metric | Forbidden inference |
|---|---|---|---|
| Bee | Content-addressed source-span ingestion and deterministic normalization | Source/span hash preservation | Repetition or similarity implies truth |
| Empress | Generative extension and exact finite coboundary \(d\) | Typed obligations and exact edge residuals | \(d^2=0\) without a specified flat complex |
| Pandora | Boundary, mutation, and counterexample generation | Replayable witness yield and hypothesis coverage | Search failure implies truth |
| Emperor | Constraint/dependency audit and exact transpose adjoint \(d^\*\) | Blockers and adjoint-law residual | Audit or symbolic contraction certifies a theorem |
| Topos AI | Exact finite cover, restriction, and overlap comparison | Coverage deficit and explicit overlap obstruction | Resemblance or an incomplete cover glues globally |
| Bordon Symphony | Ten-phase compatibility cycle and rational connection energy | Residual, energy, holonomy metadata, phase trace | Low energy implies mathematical truth |
| UTAI | Pre-mortem, disconfirmation, negative-result and baseline ledger | Risk coverage and baseline comparison | Governance or closure policy is a theorem |

Every Bordon run records:

`INHALE → SUPERPOSE → ANNEAL → HOLOPORT → EXHALE → LISTEN → MEASURE HOLONOMY → REGLUE → MOVE FRAME → CONTINUE`.

## Certification boundary

Research artifacts cannot carry `proved` or `refuted` as an internal status.
A final verdict is a separate `PromotedArtifact` envelope.

Acceptance requires:

- an artifact registered in the gate-side, content-addressed lineage store;
- an allowed status transition and monotone hypotheses, remainder, constraints,
  evidence, phase trace, and route history;
- a theorem-specific external verifier object installed in the gate;
- no proof-critical unresolved hypotheses or obligations;
- for prose claims, a distinct formalization-adequacy verifier;
- distinct producer, proof-verifier, and adequacy-verifier principals;
- a replay recipe, environment digest, and exact certificate digest;
- an Ed25519 signature from the configured promotion gate;
- verification of that signature using the trusted public key.

The Ed25519 private key must live in an isolated promotion process in an
adversarial deployment. Research nodes and UI consumers receive only the
public key.

## Lean boundary

`LambdaSatSolver/VDIS/ProofDistillation.lean` is an import-free structural
shadow. It proves only:

- a research-node event cannot be a verified-event constructor;
- every proved envelope contains an external attestation;
- the complete Bordon cycle contains ten phases.

Exact-module replay reports no axioms for all three declarations.

The current Lean adapter accepts only an exact, import-free source snapshot.
It rejects `import`, `public import`, and `private import`. Imported theorem
modules require a future isolated clean-build verifier that content-addresses
the dependency closure. A root `lake build` is insufficient because Lean
accepts `sorry`, and the current VDIS root still contains two active
placeholders in `TuringHalting_Master.lean`.

## SAT boundary

The existing strict DRAT checker is reusable for exact CNF bytes. The mesh
adapter snapshots both the CNF and proof bytes to prevent time-of-check /
time-of-use changes.

It nevertheless remains diagnostic-only: a DRAT proof establishes that the
CNF is UNSAT, not that the CNF faithfully encodes an arbitrary mathematical
claim. Promotion stays disabled until a separately trust-anchored
claim-to-CNF adequacy certificate exists. The current LRAT wrapper is also
excluded because it accepts a bare zero process exit code.

## Erdős #269 experiment

The first distillation run processed five claims:

| Claim | Mesh status | Main obstruction |
|---|---|---|
| Two-prime transcendence theorem | Proof candidate | External theorem normalization, formalization, and kernel replay remain |
| Full resolution for every finite \(|P|\ge2\) | Candidate | No \(|P|\ge3\) irrationality theorem |
| Carry is a flat associative two-cocycle | Proof candidate | Formal declaration absent; supplied associator chart conflicts with corrected chart |
| Multipoint lattice series as weighted #CSP/#SAT | Candidate | Analytic-completion chart is uncovered |
| Torus–tail–Diophantine–certified-search route | Candidate research program | Uniform Diophantine bound is open |

Topos AI refused both an explicit overlap contradiction and an incomplete
cover. Every claim retained its unresolved remainder. No Erdős claim was
promoted.

## Verification

From the repository root:

```bash
python3 -m pytest backend/tests/test_proof_mesh.py -q
lake env lean LambdaSatSolver/VDIS/ProofDistillation.lean
```

Current result:

- 34 Python tests passed;
- all three Lean firewall declarations compiled and reported no axioms;
- an end-to-end exact-source replay produced a publicly verifiable Ed25519
  envelope for the firewall theorem;
- that envelope explicitly retains the remainder: it proves no Erdős claim.

Run the current Erdős distillation:

```bash
python3 -m backend.proof_mesh \
  /Users/jesusvilelajato/Documents/Codex/2026-07-24/last-login-fri-jul-24-12/work/erdos269_proof_mesh_config.json \
  --output /Users/jesusvilelajato/Documents/Codex/2026-07-24/last-login-fri-jul-24-12/outputs/erdos269_proof_mesh_run.json \
  --ledger /Users/jesusvilelajato/Documents/Codex/2026-07-24/last-login-fri-jul-24-12/outputs/erdos269_proof_mesh_ledger.jsonl
```

## Files

- `backend/proof_mesh/artifacts.py` — immutable candidates, monotone remainder,
  content hashes, epistemic transitions.
- `backend/proof_mesh/nodes.py` — seven node implementations and exact finite
  diagnostics.
- `backend/proof_mesh/orchestrator.py` — local routing.
- `backend/proof_mesh/ledger.py` — append-only run ledger and gate-side lineage
  store.
- `backend/proof_mesh/verifiers.py` — exact-source Lean replay, diagnostic DRAT
  replay, distinct adequacy path, Ed25519 promotion envelope.
- `backend/tests/test_proof_mesh.py` — adversarial and mathematical regression
  suite.
- `LambdaSatSolver/VDIS/ProofDistillation.lean` — narrow formal firewall
  shadow.

## Honest deployment boundary

This is a working local experiment, not yet a distributed service mesh.
Production distribution still needs isolated node processes, a durable signed
artifact store, an isolated promotion service, stable public-key management,
and an isolated clean Lean dependency build.
